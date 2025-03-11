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
        from database.schema import Device
        from database.models import get_session
        
        session = get_session(config['database_path'])
        try:
            devices = session.query(Device).all()
            return jsonify([device.to_dict() for device in devices])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            session.close()

    # Device registration endpoint
    @app.route('/devices/register', methods=['POST'])
    def register_device():
        """Register a new device or update an existing one."""
        try:
            device_data = request.json
            
            if not device_data or not all(k in device_data for k in ['device_id', 'hostname']):
                return jsonify({"error": "Missing required device information"}), 400
            
            from database.models import get_session, Device
            
            session = get_session(config['database_path'])
            try:
                # Check if device already exists
                existing_device = session.query(Device).filter_by(device_id=device_data['device_id']).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.hostname = device_data['hostname']
                    existing_device.last_seen = datetime.now()
                    message = "Device updated"
                    status_code = 200
                else:
                    # Create new device
                    new_device = Device(
                        device_id=device_data['device_id'],
                        hostname=device_data['hostname'],
                        last_seen=datetime.now()
                    )
                    session.add(new_device)
                    message = "Device registered"
                    status_code = 201
                
                session.commit()
                return jsonify({"message": message, "device_id": device_data['device_id']}), status_code
                
            except Exception as e:
                session.rollback()
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Modify the system metrics endpoint to only accept PUT requests
    @app.route('/metrics/system', methods=['PUT'])
    def system_metrics_endpoint():
        """
        PUT: Receive and store system metrics from a device
        """
        try:
            payload = request.json
            
            if not payload or 'device_id' not in payload or 'metrics' not in payload:
                return jsonify({"error": "Missing required data"}), 400
            
            device_id = payload['device_id']
            metrics = payload['metrics']
            
            # Store each metric in the database
            for metric_name, metric_value in metrics.items():
                if metric_name in config['system_metrics']:
                    insert_system_metric(
                        config['database_path'],
                        metric_name,
                        metric_value,
                        device_id=device_id
                    )
            
            # Update device last_seen timestamp
            from database.models import get_session, Device
            session = get_session(config['database_path'])
            try:
                device = session.query(Device).filter_by(device_id=device_id).first()
                if device:
                    device.last_seen = datetime.now()
                    session.commit()
            except Exception as e:
                session.rollback()
                app.logger.error(f"Error updating device last_seen: {e}")
            finally:
                session.close()
            
            return jsonify({"message": "Metrics stored successfully"}), 200
            
        except Exception as e:
            app.logger.error(f"Error in PUT /metrics/system: {e}")
            return jsonify({"error": str(e)}), 500

    # System metrics history with device filter
    @app.route('/metrics/system/history/<metric_name>', methods=['GET'])
    def get_system_metrics_history_endpoint(metric_name):
        # Check for device_id in request args
        device_id = request.args.get('device_id', None)  # Remove DEVICE_ID default
        
        # Fetch the history for this metric from the database for the specified device
        history = get_system_metrics_history(config['database_path'], metric_name, device_id=device_id)
        
        # Return as JSON
        return jsonify(history)

    # New endpoint to get latest system metrics for a device
    @app.route('/metrics/system/latest', methods=['GET'])
    def get_latest_system_metrics():
        """Get the latest system metrics for a specific device."""
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        metrics = fetch_latest_system_metrics(config['database_path'], device_id=device_id)
        return jsonify(metrics)

    # Endpoint: Get stock data
    @app.route('/metrics/stock/<symbol>', methods=['GET', 'PUT'])
    def get_stock_data(symbol):
        """Get or update stock data for a specific symbol."""
        if request.method == 'GET':
            # Return the latest stock data for the symbol
            stock_data = fetch_latest_stock_data(config['database_path'], symbol)
            if stock_data:
                return jsonify(stock_data)
            else:
                return jsonify({"error": f"No data found for symbol: {symbol}"}), 404
        
        elif request.method == 'PUT':
            # Client sending stock data
            try:
                data = request.get_json()
                if not data or 'price' not in data:
                    return jsonify({"error": "Missing required fields"}), 400
                
                # Store the stock data
                price = data['price']
                insert_stock_data(config['database_path'], symbol, price)
                
                return jsonify({"success": True, "message": f"Stock data for {symbol} updated successfully"})
            except Exception as e:
                return jsonify({"error": f"Failed to update stock data: {str(e)}"}), 500

    # Endpoint: Poll for pending stock symbol
    @app.route('/metrics/stock/poll', methods=['GET'])
    def poll_stock_symbol():
        """
        Endpoint for clients to poll for pending stock symbols.
        Returns the pending symbol if available, then resets it to None.
        """
        global pending_stock_symbol
        
        # Get the device_id from the request
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # If there's a pending symbol, return it and reset
        if pending_stock_symbol:
            symbol = pending_stock_symbol
            pending_stock_symbol = None  # Reset after it's been polled
            return jsonify({"symbol": symbol})
        
        # No pending symbol
        return jsonify({"symbol": None})

    # Endpoint: Set pending stock symbol
    @app.route('/metrics/stock/set_pending', methods=['POST'])
    def set_pending_stock_symbol():
        """
        Endpoint for the dashboard to set a pending stock symbol for clients to poll.
        Only sets the symbol for polling without adding it to the database.
        """
        global pending_stock_symbol
        
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415
        
        symbol = request.json.get('symbol')
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
        
        # Standardize the symbol format (uppercase)
        symbol = symbol.upper().strip()
        
        # Set the pending symbol
        pending_stock_symbol = symbol
        
        return jsonify({
            "success": True,
            "message": f"Pending stock symbol set to {symbol}"
        })

    # Endpoint: Get distinct stock symbols
    @app.route('/metrics/stock/symbols', methods=['GET'])
    def get_stock_symbols():
        symbols = fetch_stock_symbols(config['database_path'])
        return jsonify(symbols)

    # Endpoint: Get historical stock data
    @app.route('/metrics/stock/history/<symbol>', methods=['GET'])
    def get_stock_history_endpoint(symbol):
        history = get_stock_history(config['database_path'], symbol)
        return jsonify(history)

    return app
