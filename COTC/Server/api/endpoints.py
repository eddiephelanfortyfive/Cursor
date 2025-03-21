from flask import jsonify, request
import json
import requests
from datetime import datetime
from database.models import (
    insert_system_metric, insert_stock_data,
    fetch_latest_system_metrics, fetch_latest_stock_data,
    fetch_stock_symbols, get_stock_history, init_database as init_db,
    get_system_metrics_history
)
import logging
import os
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

# Configure Werkzeug logger to reduce terminal clutter
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Global variable to store the pending stock symbol
pending_stock_symbol = None

# Direct access functions to get and set the pending stock symbol
def get_pending_stock_symbol():
    """Get the current pending stock symbol."""
    global pending_stock_symbol
    return pending_stock_symbol

def set_pending_stock_symbol_direct(symbol):
    """
    Set the pending stock symbol directly.
    
    Args:
        symbol (str): The stock symbol to set as pending.
        
    Returns:
        dict: A dictionary with success status and message.
    """
    global pending_stock_symbol
    
    if not symbol:
        return {"success": False, "error": "Symbol is required"}
    
    # Standardize the symbol format (uppercase)
    symbol = symbol.upper().strip()
    
    # Set the pending symbol
    pending_stock_symbol = symbol
    
    return {
        "success": True,
        "message": f"Pending stock symbol set to {symbol}"
    }

def reset_pending_stock_symbol():
    """Reset the pending stock symbol to None."""
    global pending_stock_symbol
    symbol = pending_stock_symbol
    pending_stock_symbol = None
    return symbol

def register_routes(app, config):
    """Register all routes with the Flask app"""
    
    # Function to check if all required tables exist in the database
    def check_tables_exist(db_path):
        from database.schema import get_engine
        try:
            engine = get_engine(db_path)
            inspector = inspect(engine)
            required_tables = ['devices', 'metric_types', 'system_metrics', 'stock_symbols', 'stock_data']
            existing_tables = inspector.get_table_names()
            
            for table in required_tables:
                if table not in existing_tables:
                    logging.warning(f"Required table '{table}' does not exist in the database")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Error checking tables in database: {e}")
            return False

    # Initialize database with proper table verification
    init_flag_file = Path(config['database_path']).parent / '.db_initialized'
    tables_exist = check_tables_exist(config['database_path'])

    if os.path.exists(init_flag_file) and tables_exist:
        logging.info("Database already initialized (found flag file and tables exist), skipping reinitialization.")
    else:
        if os.path.exists(init_flag_file) and not tables_exist:
            logging.warning("Found initialization flag but tables are missing. Re-initializing database...")
            try:
                os.remove(init_flag_file)
            except:
                pass
            
        logging.info("Initializing database...")
        try:
            init_db(config['database_path'])
            with open(init_flag_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logging.error(f"Error initializing database: {e}")

    # Route definitions
    @app.route('/devices', methods=['GET'])
    def get_devices():
        """Get all registered devices"""
        from database.schema import Device
        from database.models import get_session
        
        session = get_session(config['database_path'])
        try:
            devices = session.query(Device).all()
            logging.warning(f"Retrieved devices: {[{d.device_id: d.hostname} for d in devices]}")
            return jsonify([device.to_dict() for device in devices])
        except Exception as e:
            logging.error(f"Error getting devices: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            session.close()

    # Device registration endpoint
    @app.route('/devices/register', methods=['POST'])
    def register_device():
        """Register a new device or update an existing one."""
        try:
            device_data = request.json
            logging.warning(f"Registering device with data: {device_data}")
            
            if not device_data or not all(k in device_data for k in ['device_id', 'hostname', 'mac_address']):
                return jsonify({"error": "Missing required device information (device_id, hostname, and mac_address are required)"}), 400
            
            from database.models import get_session
            from database.schema import Device
            
            session = get_session(config['database_path'])
            try:
                # First check if a device with this MAC address already exists
                existing_device_by_mac = session.query(Device).filter_by(mac_address=device_data['mac_address']).first()
                
                if existing_device_by_mac:
                    # Device with this MAC already exists - update it
                    logging.warning(f"Found device with MAC address {device_data['mac_address']}, updating it")
                    existing_device_by_mac.hostname = device_data['hostname']
                    existing_device_by_mac.last_seen = datetime.now()
                    # Update device_id if it's different (client might have generated a new one)
                    if existing_device_by_mac.device_id != device_data['device_id']:
                        logging.warning(f"Updating device_id from {existing_device_by_mac.device_id} to {device_data['device_id']}")
                        existing_device_by_mac.device_id = device_data['device_id']
                    message = "Device updated by MAC address"
                    status_code = 200
                    
                    session.commit()
                    return jsonify({
                        "message": message,
                        "device_id": existing_device_by_mac.device_id,
                        "mac_address": existing_device_by_mac.mac_address,
                        "hostname": existing_device_by_mac.hostname
                    }), status_code
                
                # If no device with this MAC exists, check if device_id exists
                existing_device = session.query(Device).filter_by(device_id=device_data['device_id']).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.hostname = device_data['hostname']
                    existing_device.last_seen = datetime.now()
                    # Update MAC address if it's different
                    if existing_device.mac_address != device_data['mac_address']:
                        logging.warning(f"Updating MAC address from {existing_device.mac_address} to {device_data['mac_address']}")
                        existing_device.mac_address = device_data['mac_address']
                    message = "Device updated"
                    status_code = 200
                    logging.warning(f"Updated existing device: {existing_device.device_id}")
                else:
                    # Create new device
                    new_device = Device(
                        device_id=device_data['device_id'],
                        mac_address=device_data['mac_address'],
                        hostname=device_data['hostname'],
                        last_seen=datetime.now()
                    )
                    session.add(new_device)
                    message = "Device registered"
                    status_code = 201
                    logging.warning(f"Created new device: {new_device.device_id} with MAC: {new_device.mac_address}")
                
                session.commit()
                
                # Verify the device was saved
                saved_device = session.query(Device).filter_by(device_id=device_data['device_id']).first()
                logging.warning(f"Verified saved device: {saved_device.device_id if saved_device else 'Not found'}")
                
                return jsonify({
                    "message": message,
                    "device_id": device_data['device_id'],
                    "mac_address": device_data['mac_address'],
                    "hostname": device_data['hostname']
                }), status_code
                
            except Exception as e:
                session.rollback()
                logging.error(f"Database error during device registration: {e}")
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()
            
        except Exception as e:
            logging.error(f"Error in device registration: {e}")
            return jsonify({"error": str(e)}), 500

    # Modify the system metrics endpoint to only accept PUT requests
    @app.route('/metrics/system', methods=['PUT'])
    def system_metrics_endpoint():
        """
        PUT: Receive and store system metrics from a device
        """
        try:
            payload = request.json
            
            if not payload or 'metrics' not in payload:
                return jsonify({"error": "Missing required data"}), 400
            
            # Get identifiers
            device_id = payload.get('device_id')
            mac_address = payload.get('mac_address')
            hostname = payload.get('hostname')
            
            # Need at least MAC address or device_id
            if not mac_address and not device_id:
                return jsonify({"error": "Either mac_address or device_id is required"}), 400
            
            metrics = payload['metrics']
            
            # Find the device by MAC address first
            from database.models import get_session, Device
            from database.schema import get_or_create_device
            
            session = get_session(config['database_path'])
            try:
                # Try to find the device
                device = None
                
                # Check by MAC address first
                if mac_address:
                    device = session.query(Device).filter_by(mac_address=mac_address).first()
                
                # If not found by MAC or MAC not provided, try by device_id
                if not device and device_id:
                    device = session.query(Device).filter_by(device_id=device_id).first()
                
                # If still not found but we have MAC, create a new device
                if not device and mac_address:
                    logging.warning(f"Creating new device for MAC: {mac_address}")
                    device = get_or_create_device(session, device_id=None, mac_address=mac_address, hostname=hostname)
                    session.add(device)
                    session.flush()  # Generate ID
                elif not device:
                    return jsonify({"error": "Device not found and insufficient information to create one"}), 400
                
                # Now we have a valid device, we can store metrics
                device_id_for_metrics = device.device_id
                
                # Update device last_seen timestamp
                device.last_seen = datetime.now()
                session.commit()
                
                # Store each metric in the database
                for metric_name, metric_value in metrics.items():
                    if metric_name in config['system_metrics']:
                        # Using the found/created device's ID to store metrics
                        insert_system_metric(
                            config['database_path'],
                            metric_name,
                            metric_value,
                            device_id=device_id_for_metrics,
                            mac_address=mac_address
                        )
                
                return jsonify({"message": "Metrics stored successfully"}), 200
                
            except Exception as e:
                session.rollback()
                app.logger.error(f"Error processing system metrics: {e}")
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()
            
        except Exception as e:
            app.logger.error(f"Error in PUT /metrics/system: {e}")
            return jsonify({"error": str(e)}), 500


    # Endpoint: Poll for pending stock symbol
    @app.route('/metrics/stock/poll', methods=['GET'])
    def poll_stock_symbol():
        """
        Endpoint for clients to poll for pending stock symbols.
        Returns the pending symbol if available, then resets it to None.
        """
        # Get identifiers from the request
        device_id = request.args.get('device_id')
        mac_address = request.args.get('mac_address')
        hostname = request.args.get('hostname')
        
        # Need at least one identifier
        if not (device_id or mac_address):
            return jsonify({"error": "Either mac_address or device_id is required"}), 400
        
        # Verify device exists
        from database.models import get_session
        from database.schema import Device, get_or_create_device
        
        session = get_session(config['database_path'])
        try:
            # Try to find the device
            device = None
            
            # Check by MAC address first
            if mac_address:
                device = session.query(Device).filter_by(mac_address=mac_address).first()
            
            # If not found by MAC or MAC not provided, try by device_id
            if not device and device_id:
                device = session.query(Device).filter_by(device_id=device_id).first()
            
            # If still not found but we have MAC, create a new device
            if not device and mac_address:
                logging.warning(f"Creating new device for MAC: {mac_address}")
                device = get_or_create_device(session, device_id=None, mac_address=mac_address, hostname=hostname)
                session.add(device)
                session.commit()
            elif not device:
                return jsonify({"error": "Device not found and insufficient information to create one"}), 400
            
            # Device found or created, proceed with polling
            # Get the current pending symbol
            symbol = get_pending_stock_symbol()
            
            # If there's a pending symbol, return it and reset
            if symbol:
                # Reset the pending symbol
                reset_pending_stock_symbol()
                return jsonify({"symbol": symbol})
            
            # No pending symbol
            return jsonify({"symbol": None})
            
        except Exception as e:
            session.rollback()
            app.logger.error(f"Error in poll_stock_symbol: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            session.close()

    # Update the stock metrics endpoint to support both formats
    @app.route('/metrics/stock/<symbol>', methods=['PUT'])
    def stock_metrics_endpoint_with_symbol(symbol):
        """
        PUT: Receive and store stock metrics from a client with symbol in URL
        The price should be in the JSON payload
        Expected payload format:
        {
            "price": float
        }
        """
        try:
            payload = request.json or {}
            
            # Clean the symbol
            symbol = symbol.upper().strip() if symbol else None
            
            if not symbol:
                return jsonify({"error": "Symbol is required in the URL"}), 400
                
            # Get price from payload
            if 'price' not in payload:
                return jsonify({"error": "Price is required in the request body"}), 400
                
            # Validate price
            try:
                price = float(payload['price'])
                if price <= 0:
                    return jsonify({"error": "Price must be a positive number"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Price must be a valid number"}), 400
            
            # Insert the stock data
            success = insert_stock_data(
                config['database_path'],
                symbol,
                price
            )
            
            if success:
                # Also add/update the symbol in the stock symbols table
                from database.models import get_session
                from database.schema import StockSymbol
                
                session = get_session(config['database_path'])
                try:
                    # Check if symbol already exists
                    stock_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
                    if not stock_symbol:
                        # Add new symbol
                        stock_symbol = StockSymbol(symbol=symbol)
                        session.add(stock_symbol)
                        session.commit()
                        app.logger.info(f"Added new stock symbol: {symbol}")
                except Exception as e:
                    session.rollback()
                    app.logger.error(f"Error updating stock symbol: {e}")
                finally:
                    session.close()
                
                return jsonify({"message": f"Stock data for {symbol} stored successfully"}), 200
            else:
                return jsonify({"error": f"Failed to store stock data for {symbol}"}), 500
            
        except Exception as e:
            app.logger.error(f"Error in PUT /metrics/stock/{symbol}: {e}")
            return jsonify({"error": str(e)}), 500


    # Add the original endpoint to support both formats
    @app.route('/metrics/stock', methods=['PUT'])
    def stock_metrics_endpoint():
        """
        PUT: Receive and store stock metrics from a client
        Expected JSON payload:
        {
            "device_id": "string", // optional
            "symbol": "string",    // required - stock symbol
            "price": float         // required - current stock price
        }
        """
        try:
            payload = request.json
            
            if not payload or 'symbol' not in payload or 'price' not in payload:
                return jsonify({"error": "Missing required data (symbol and/or price)"}), 400
            
            symbol = payload['symbol'].upper().strip()
            
            # Validate price
            try:
                price = float(payload['price'])
                if price <= 0:
                    return jsonify({"error": "Price must be a positive number"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Price must be a valid number"}), 400
            
            # Insert the stock data
            success = insert_stock_data(
                config['database_path'],
                symbol,
                price
            )
            
            if success:
                # Also add/update the symbol in the stock symbols table
                from database.models import get_session
                from database.schema import StockSymbol
                
                session = get_session(config['database_path'])
                try:
                    # Check if symbol already exists
                    stock_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
                    if not stock_symbol:
                        # Add new symbol
                        stock_symbol = StockSymbol(symbol=symbol)
                        session.add(stock_symbol)
                        session.commit()
                        app.logger.info(f"Added new stock symbol: {symbol}")
                except Exception as e:
                    session.rollback()
                    app.logger.error(f"Error updating stock symbol: {e}")
                finally:
                    session.close()
                
                return jsonify({"message": f"Stock data for {symbol} stored successfully"}), 200
            else:
                return jsonify({"error": f"Failed to store stock data for {symbol}"}), 500
            
        except Exception as e:
            app.logger.error(f"Error in PUT /metrics/stock: {e}")
            return jsonify({"error": str(e)}), 500

