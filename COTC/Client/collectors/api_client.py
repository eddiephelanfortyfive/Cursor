"""
API Client

This module handles communication with the monitoring server API.
"""
import requests
import logging
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class APIClient:
    def __init__(self, server_url):
        """
        Initialize the API client.
        
        Args:
            server_url: The URL of the monitoring server
        """
        self.server_url = server_url
        self.session = requests.Session()
        self.timeout = 5  # 5 second timeout for all requests
    
    def _make_request(self, method, endpoint, **kwargs):
        """
        Make an HTTP request with error handling.
        
        Args:
            method: HTTP method (get, post, put, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if request failed
        """
        url = f"{self.server_url}{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                verify=False,  # Disable SSL verification for development
                **kwargs
            )
            return response
        except RequestException as e:
            logging.warning(f"Request failed: {e}")
            return None
    
    def register_device(self, device_info):
        """
        Register this device with the server.
        
        Args:
            device_info: Dictionary with device information
            
        Returns:
            True if successful, False otherwise
        """
        logging.info(f"Sending registration request with data: {device_info}")
        
        # First try the newer endpoint that expects hostname and MAC address
        response = self._make_request('POST', '/devices/register', json=device_info)
        
        if response and (response.status_code == 200 or response.status_code == 201):
            logging.info(f"Device registered successfully: {device_info['hostname']}")
            return True
        else:
            # If that fails, try a backup approach - use the metrics endpoint directly
            # This will create the device record if it doesn't exist
            metrics = {"cpu_usage": 0, "ram_usage": 0}  # Dummy metrics
            metrics_payload = {
                "hostname": device_info["hostname"],
                "mac_address": device_info["mac_address"],
                "metrics": metrics
            }
            
            metrics_response = self._make_request('PUT', '/metrics/system', json=metrics_payload)
            
            if metrics_response and metrics_response.status_code == 200:
                logging.info(f"Device registered via metrics endpoint: {device_info['hostname']}")
                return True
            else:
                if response:
                    try:
                        error_text = response.text
                        try:
                            error_json = response.json()
                            logging.error(f"Failed to register device: {response.status_code} - {error_json}")
                        except:
                            logging.error(f"Failed to register device: {response.status_code} - {error_text}")
                    except:
                        logging.error(f"Failed to register device: {response.status_code} - Unable to read response")
                else:
                    logging.error("Failed to register device: No response received")
                return False
    
    def send_system_metrics(self, hostname, mac_address, metrics):
        """
        Send system metrics to the server.
        
        Args:
            hostname: The device hostname
            mac_address: The device MAC address
            metrics: Dictionary of metrics to send
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "hostname": hostname,
            "mac_address": mac_address,
            "metrics": metrics
        }
        
        response = self._make_request('PUT', '/metrics/system', json=payload)
        
        if response and response.status_code == 200:
            logging.info(f"System metrics sent successfully: {metrics}")
            return True
        else:
            if response:
                logging.error(f"Failed to send system metrics: {response.status_code} - {response.text}")
            return False
    
    def send_stock_data(self, symbol, price):
        """
        Send stock data to the server.
        
        Args:
            symbol: Stock symbol
            price: Current price
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "symbol": symbol,
            "price": price
        }
        
        response = self._make_request('PUT', f'/metrics/stock/{symbol}', json=payload)
        
        if response and response.status_code == 200:
            logging.info(f"Stock data sent successfully: {symbol}=${price}")
            return True
        else:
            if response:
                logging.error(f"Failed to send stock data: {response.status_code} - {response.text}")
            return False
    
    def poll_stock_symbols(self, hostname, mac_address):
        """
        Poll the server for pending stock symbols.
        
        Args:
            hostname: The device hostname
            mac_address: The device MAC address
            
        Returns:
            Stock symbol (str) if available, None otherwise
        """
        logging.info(f"Making poll request to {self.server_url}/metrics/stock/poll (hostname: {hostname}, MAC: {mac_address})")
        response = self._make_request('GET', f'/metrics/stock/poll?hostname={hostname}&mac_address={mac_address}')
        
        if response:
            logging.info(f"Poll response received - Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    symbol = data.get('symbol')
                    
                    if symbol:
                        logging.info(f"Received new stock symbol from polling: {symbol}")
                    else:
                        logging.info("Poll response: No new symbols available")
                    return symbol
                except Exception as e:
                    logging.error(f"Error parsing poll response: {e}")
                    if response.text:
                        logging.error(f"Response content: {response.text}")
            else:
                logging.warning(f"Unexpected status code from poll: {response.status_code}")
                if response.text:
                    logging.warning(f"Response content: {response.text}")
        else:
            logging.warning("No response received from polling request")
            
        return None 