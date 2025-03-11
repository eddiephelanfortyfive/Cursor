"""
Client Agent

Main module for the monitoring client that collects and sends system metrics and stock data.
"""
import json
import logging
import socket
import threading
import time
from pathlib import Path
import uuid
import subprocess
import re
from collections import namedtuple
import platform

from collectors.pc_metrics import PCMetricsCollector
from collectors.stock_collector import StockCollector
from collectors.api_client import APIClient

class ClientAgent:
    def __init__(self, config_path):
        """
        Initialize the client agent.
        
        Args:
            config_path: Path to the configuration file
        """
        self.load_config(config_path)
        self.setup_logging()
        
        # Initialize collectors and API client
        self.api_client = APIClient(self.config["server_url"])
        self.pc_metrics = PCMetricsCollector(self.config["metrics"]["enabled"])
        
        if self.config["stocks"]["api_key"]:
            self.stock_collector = StockCollector(
                self.config["stocks"]["api_key"],
                self.config["stocks"]["symbols"]
            )
        else:
            self.stock_collector = None
            logging.warning("No stock API key provided - stock collection disabled")
        
        # Get device identification
        self.device_id = str(uuid.uuid4())  # Keep for backward compatibility
        self.hostname = socket.gethostname()
        self.mac_address = self.get_mac_address()
        logging.info(f"Device identification - Hostname: {self.hostname}, MAC: {self.mac_address}")
        
        # Try to register device but don't fail if it doesn't work
        self.register_device()
        
        # Initialize threads
        self.metrics_thread = None
        self.stock_thread = None
        self.stock_polling_thread = None
        self.running = False
    
    def load_config(self, config_path):
        """Load configuration from file."""
        try:
            with open(config_path) as f:
                self.config = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            raise
    
    def setup_logging(self):
        """Configure logging."""
        level = logging.DEBUG if self.config.get("debug") else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def register_device(self, max_retries=3):
        """Register this device with the server."""
        # Create device info payload matching exactly what the server expects
        device_info = {
            # Required fields
            "hostname": self.hostname,
            "mac_address": self.mac_address,
            
            # Optional fields
            "device_id": self.device_id,
            "os_info": platform.platform()
        }
        
        logging.info(f"Registering device with server - Hostname: {self.hostname}, MAC: {self.mac_address}")
        
        for attempt in range(max_retries):
            try:
                if self.api_client.register_device(device_info):
                    logging.info(f"Successfully registered device: {self.hostname}")
                    return True
                else:
                    logging.warning(f"Failed to register device (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logging.warning(f"Error registering device (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)
        
        logging.warning("Failed to register device after all attempts. Continuing in offline mode.")
        return False
    
    def collect_and_send_metrics(self):
        """Collect and send system metrics in a loop."""
        while self.running:
            try:
                metrics = self.pc_metrics.collect_metrics()
                try:
                    self.api_client.send_system_metrics(self.hostname, self.mac_address, metrics)
                except Exception as e:
                    logging.warning(f"Failed to send metrics to server: {e}")
                    # Continue collecting metrics even if sending fails
            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.config["collection_interval"])
    
    def collect_and_send_stocks(self):
        """Collect and send stock data in a loop."""
        if not self.stock_collector:
            return
            
        while self.running:
            try:
                stock_data = self.stock_collector.collect_stock_data()
                symbols_to_remove = []
                
                for symbol, price in stock_data.items():
                    # Check if the price is 0, indicating we should remove the symbol
                    if price == 0:
                        logging.warning(f"Stock {symbol} returned price of 0, will remove from collection list")
                        symbols_to_remove.append(symbol)
                        continue
                        
                    try:
                        self.api_client.send_stock_data(symbol, price)
                    except Exception as e:
                        logging.warning(f"Failed to send stock data to server: {e}")
                        # Continue collecting stock data even if sending fails
                
                # Remove any symbols that returned a price of 0
                for symbol in symbols_to_remove:
                    self.remove_stock_symbol(symbol)
                    
            except Exception as e:
                logging.error(f"Error collecting stock data: {e}")
            
            time.sleep(self.config["stock_interval"])
    
    def poll_and_process_stock_symbols(self):
        """Poll for new stock symbols and add them to the collector."""
        if not self.stock_collector:
            logging.warning("Stock collector not initialized, polling thread exiting")
            return
            
        # Use a shorter polling interval for stock symbols (5 seconds)
        polling_interval = 5
        
        logging.info(f"Starting stock symbol polling in thread {threading.current_thread().name}")
        poll_count = 0
        
        while self.running:
            poll_count += 1
            logging.info(f"Poll cycle #{poll_count} started in thread {threading.current_thread().name}")
            
            try:
                # Poll for new stock symbols
                logging.debug(f"Making poll request to server (Hostname: {self.hostname}, MAC: {self.mac_address})")
                symbol = self.api_client.poll_stock_symbols(self.hostname, self.mac_address)
                
                if symbol:
                    logging.info(f"Processing new stock symbol: {symbol}")
                    # Log current stock list before adding
                    current_symbols = self.stock_collector.stocks_to_collect
                    logging.info(f"Current stock symbols being monitored: {current_symbols}")
                    
                    # Add the symbol to our stock collector
                    self.stock_collector.add_stock(symbol)
                    
                    # Log updated stock list
                    updated_symbols = self.stock_collector.stocks_to_collect
                    logging.info(f"Updated stock symbols list: {updated_symbols}")
                    
                    # Update the config file with the new symbol
                    self.update_config_with_new_symbol(symbol)
                else:
                    logging.info(f"Poll cycle #{poll_count}: No new symbols")
            except Exception as e:
                logging.error(f"Error in poll cycle #{poll_count}: {e}", exc_info=True)
            
            logging.debug(f"Poll cycle #{poll_count} completed, waiting {polling_interval} seconds")
            time.sleep(polling_interval)
            
        logging.info("Polling thread exiting (self.running = False)")
    
    def update_config_with_new_symbol(self, symbol):
        """
        Update the configuration file with a new stock symbol.
        
        Args:
            symbol: Stock symbol to add to the config
        """
        try:
            # Make sure the symbol is uppercase
            symbol = symbol.upper()
            
            # Check if the symbol is already in the config
            if symbol in self.config["stocks"]["symbols"]:
                return
                
            # Add the symbol to the config
            self.config["stocks"]["symbols"].append(symbol)
            
            # Save the updated config
            config_path = Path(__file__).parent / "client_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
                
            logging.info(f"Updated configuration file with new stock symbol: {symbol}")
        except Exception as e:
            logging.error(f"Failed to update config with new symbol: {e}")
    
    def remove_stock_symbol(self, symbol):
        """
        Remove a stock symbol from the collection list.
        
        Args:
            symbol: Stock symbol to remove
        """
        try:
            # Make sure the symbol is uppercase for consistency
            symbol = symbol.upper()
            
            # Remove from stock collector if it exists
            if symbol in self.stock_collector.stocks_to_collect:
                self.stock_collector.stocks_to_collect.remove(symbol)
                logging.info(f"Removed {symbol} from stock collection list")
                logging.info(f"Updated stock symbols list: {self.stock_collector.stocks_to_collect}")
            else:
                logging.warning(f"Symbol {symbol} not found in collection list, nothing to remove")
                
            # Also remove from config if it exists there
            if symbol in self.config["stocks"]["symbols"]:
                self.config["stocks"]["symbols"].remove(symbol)
                
                # Save the updated config
                config_path = Path(__file__).parent / "client_config.json"
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=4)
                    
                logging.info(f"Removed {symbol} from configuration file")
        except Exception as e:
            logging.error(f"Error removing stock symbol {symbol}: {e}", exc_info=True)
    
    def start(self):
        """Start the client agent."""
        self.running = True
        
        # Start metrics collection thread
        self.metrics_thread = threading.Thread(
            target=self.collect_and_send_metrics,
            daemon=True
        )
        self.metrics_thread.start()
        logging.info("Started metrics collection thread")
        
        # Start stock collection thread if enabled
        if self.stock_collector:
            self.stock_thread = threading.Thread(
                target=self.collect_and_send_stocks,
                daemon=True
            )
            self.stock_thread.start()
            logging.info("Started stock collection thread")
            
            # Start stock symbol polling thread
            self.stock_polling_thread = threading.Thread(
                target=self.poll_and_process_stock_symbols,
                name="StockPollingThread",
                daemon=True
            )
            self.stock_polling_thread.start()
            logging.info(f"Started stock symbol polling thread (interval: 5 seconds)")
            
            # Log thread status
            logging.info(f"Active threads: Metrics={self.metrics_thread.is_alive()}, "
                        f"Stocks={self.stock_thread.is_alive()}, "
                        f"Polling={self.stock_polling_thread.is_alive()}")
        
        logging.info(f"Client agent started for device: {self.hostname}")
    
    def stop(self):
        """Stop the client agent."""
        self.running = False
        
        if self.metrics_thread:
            self.metrics_thread.join()
        
        if self.stock_thread:
            self.stock_thread.join()
            
        if self.stock_polling_thread:
            self.stock_polling_thread.join()
        
        logging.info("Client agent stopped")

    def get_mac_address(self):
        """Get the MAC address of the primary network interface."""
        try:
            # Platform-specific commands to get MAC address
            system = platform.system()
            
            if system == "Windows":
                # Windows
                output = subprocess.check_output("ipconfig /all").decode('utf-8')
                for line in output.split('\n'):
                    if "Physical Address" in line:
                        mac_address = line.split(':')[1].strip()
                        return mac_address
                        
            elif system == "Darwin":  # macOS
                # macOS - get first available en* interface (usually en0 is the built-in)
                try:
                    # First try to get the MAC address of en0 (usually the main interface)
                    output = subprocess.check_output(["ifconfig", "en0"]).decode('utf-8')
                    mac_match = re.search(r'ether\s+([0-9a-fA-F:]+)', output)
                    if mac_match:
                        return mac_match.group(1)
                except subprocess.CalledProcessError:
                    # If en0 doesn't exist, try to find any en* interface
                    try:
                        output = subprocess.check_output(["ifconfig"]).decode('utf-8')
                        # Look for en* interfaces
                        interfaces = re.findall(r'(en\d+):', output)
                        for interface in interfaces:
                            try:
                                output = subprocess.check_output(["ifconfig", interface]).decode('utf-8')
                                mac_match = re.search(r'ether\s+([0-9a-fA-F:]+)', output)
                                if mac_match:
                                    return mac_match.group(1)
                            except:
                                continue
                    except:
                        pass
                    
            elif system == "Linux":
                # Linux
                output = subprocess.check_output(["ip", "link", "show"]).decode('utf-8')
                mac_match = re.search(r'link/ether\s+([0-9a-fA-F:]+)', output)
                if mac_match:
                    return mac_match.group(1)
            
            # If we get here, we couldn't find the MAC address with platform-specific methods
            # Try a more generic approach
            NetworkInterface = namedtuple('NetworkInterface', ['name', 'mac'])
            addresses = []
            
            # Get all network interfaces
            for interface in socket.if_nameindex():
                try:
                    mac = subprocess.check_output(["ifconfig", interface[1]]).decode('utf-8')
                    mac_match = re.search(r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', mac)
                    if mac_match:
                        addresses.append(NetworkInterface(interface[1], mac_match.group(0)))
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
            
            # Filter out loopback and return the first physical interface
            for interface in addresses:
                if not interface.name.startswith('lo'):
                    return interface.mac
            
            # Last resort: Use a dummy MAC address
            logging.warning("Could not determine MAC address, using a dummy value")
            return "00:00:00:00:00:01"
        except Exception as e:
            logging.warning(f"Failed to get MAC address: {e}")
            return "00:00:00:00:00:01"  # Return a dummy MAC address instead of "Unknown"

def main():
    """Main entry point."""
    config_path = Path(__file__).parent/ "client_config.json"
    
    try:
        agent = ClientAgent(config_path)
        agent.start()
        
        # Keep main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        agent.stop()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 