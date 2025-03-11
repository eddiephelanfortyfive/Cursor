from dash.dependencies import Input, Output, State
import logging
import random
from dashboard.app import app
from database.models import get_session
from database.schema import Device
from sqlalchemy import create_engine
import json
import os
from pathlib import Path
from sqlalchemy.orm import sessionmaker

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Get the absolute path to the project root directory
PROJECT_ROOT = Path(__file__).parents[2].resolve()

# Load configuration
config_path = PROJECT_ROOT / 'config' / 'config.json'
with open(config_path) as config_file:
    config = json.load(config_file)

# Update database path to be absolute
if not os.path.isabs(config['database_path']):
    DATABASE_PATH = str(PROJECT_ROOT / config['database_path'])
else:
    DATABASE_PATH = config['database_path']

# Create database engine
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Session = sessionmaker(bind=engine)

# Callback to update the device selector dropdown
@app.callback(
    Output('device-selector', 'options'),
    [Input('device-update-interval', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_device_list(n_intervals, n_clicks):
    """Fetch all registered devices from the database and update the dropdown"""
    logger.warning("Updating device list")
    
    try:
        session = Session()
        devices = session.query(Device).all()
        logger.warning(f"Found {len(devices)} devices in database at {DATABASE_PATH}")
        
        # Create dropdown options
        options = []
        for device in devices:
            # Create a more detailed and formatted label
            hostname = device.hostname or 'Unknown'
            os_info = device.os_info or ''
            device_id = device.device_id[:8]  # First 8 chars of UUID
            
            # Format the label with more details
            if os_info:
                label = f"{hostname} - {os_info} (ID: {device_id})"
            else:
                label = f"{hostname} (ID: {device_id})"
            
            options.append({
                'label': label,
                'value': device.device_id
            })
        
        # Add a "None" option with a string value instead of null
        options.insert(0, {'label': 'No Device Selected', 'value': 'none'})
        
        return options
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return [{'label': 'No Device Selected', 'value': 'none'}]
    finally:
        session.close()

# Callback to handle device selection and update the device store
@app.callback(
    Output('device-store', 'data'),
    [Input('device-selector', 'value')]
)
def update_selected_device(selected_device_id):
    """Update the device store with the selected device information"""
    logger.warning(f"Updating device store with selected device: {selected_device_id}")
    
    if not selected_device_id or selected_device_id == 'none':
        logger.warning("No device selected")
        return {'device_id': None, 'hostname': None}
    
    try:
        session = Session()
        device = session.query(Device).filter_by(device_id=selected_device_id).first()
        
        if device:
            logger.warning(f"Found selected device: {device.hostname}")
            return {
                'device_id': device.device_id,
                'hostname': device.hostname
            }
        else:
            logger.error(f"Selected device ID {selected_device_id} not found in database")
            return {'device_id': None, 'hostname': None}
    except Exception as e:
        logger.error(f"Error fetching device details: {e}")
        return {'device_id': None, 'hostname': None}
    finally:
        session.close()

# Callback to trigger data refresh on device selection
@app.callback(
    Output('interval-component', 'n_intervals'),
    Input('device-selector', 'value')
)
def trigger_refresh_on_device_selection(selected_device):
    """Trigger an immediate refresh of all data when a device is selected"""
    if selected_device:
        logger.warning(f"Device selected: {selected_device}, triggering refresh")
        return random.randint(1, 10000)
    return 0 

@app.callback(
    [Output('device-info', 'children'),
     Output('device-info-container', 'style')],
    [Input('device-selector', 'value')]
)
def update_selected_device_info(selected_device_id):
    """Update the device information display."""
    if not selected_device_id:
        return "No device selected", {'display': 'none'}
    
    try:
        session = Session()
        device = session.query(Device).filter_by(device_id=selected_device_id).first()
        
        if device:
            info = [
                f"Device ID: {device.device_id}",
                f"Hostname: {device.hostname}",
                f"OS: {device.os_info}",
                f"Last Seen: {device.last_seen.strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            return "\n".join(info), {'display': 'block', 'whiteSpace': 'pre-line'}
        else:
            return "Device not found", {'display': 'none'}
    
    except Exception as e:
        logger.error(f"Error updating device info: {str(e)}")
        return f"Error: {str(e)}", {'display': 'block'}
    finally:
        session.close() 