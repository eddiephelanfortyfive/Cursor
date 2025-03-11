from dash.dependencies import Input, Output, State
import logging
import requests
import random
from dashboard.app import app
from dashboard.utils.config import API_BASE_URL

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Change from INFO to WARNING

# Callback to trigger data refresh on device selection
@app.callback(
    Output('interval-component', 'n_intervals'),
    Input('device-selector', 'value')
)
def trigger_refresh_on_device_selection(selected_device):
    """
    This callback triggers an immediate refresh of all data when a device is selected.
    It artificially increments the interval counter, which causes all interval-dependent
    callbacks to fire immediately.
    """
    logger.info(f"Device selected: {selected_device}, triggering refresh")
    # Return a new random value to trigger the interval-dependent callbacks
    return random.randint(1, 10000)

# Callback to update the device selector dropdown
@app.callback(
    Output('device-selector', 'options'),
    [Input('device-update-interval', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_device_list(n_intervals, n_clicks):
    """Fetch all registered devices from the API and update the dropdown"""
    logger.info(f"Updating device list, API URL: {API_BASE_URL}/devices")
    try:
        response = requests.get(f'{API_BASE_URL}/devices')
        logger.info(f"Devices API response status: {response.status_code}")
        
        if response.status_code == 200:
            devices = response.json()
            logger.info(f"Retrieved {len(devices)} devices from API")
            
            # Create dropdown options
            options = []
            for device in devices:
                # Create a more detailed and formatted label
                hostname = device.get('hostname', 'Unknown')
                os_info = device.get('os_info', '')
                device_id = device.get('device_id', '')[:8]  # First 8 chars of UUID
                
                # Format the label with more details
                if os_info:
                    label = f"{hostname} - {os_info} (ID: {device_id})"
                else:
                    label = f"{hostname} (ID: {device_id})"
                
                options.append({
                    'label': label,
                    'value': device['device_id']
                })
            
            # Add a "None" option with a string value instead of null
            options.insert(0, {'label': 'No Device Selected', 'value': 'none'})
            
            logger.info(f"Returning {len(options)} device options")
            return options
        else:
            logger.error(f"Failed to fetch devices: HTTP {response.status_code}")
            # Return at least the "None" option if API call fails
            return [{'label': 'No Device Selected', 'value': 'none'}]
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return [{'label': 'No Device Selected', 'value': 'none'}]

# Callback to handle device selection and update the device store
@app.callback(
    [Output('device-store', 'data')],
    [Input('device-selector', 'value')]
)
def update_selected_device(selected_device_id):
    """Update the device store with the selected device information"""
    logger.info(f"Updating device store with selected device: {selected_device_id}")
    
    if not selected_device_id or selected_device_id == 'none':
        # No device selected or explicitly selected "none"
        logger.info("No device selected, returning default data")
        return [{'device_id': None, 'hostname': 'No Device Selected'}]
    
    # Fetch the selected device details to get the hostname
    try:
        response = requests.get(f'{API_BASE_URL}/devices')
        if response.status_code == 200:
            devices = response.json()
            
            # Find the selected device
            selected_device = next((d for d in devices if d['device_id'] == selected_device_id), None)
            
            if selected_device:
                logger.info(f"Found selected device: {selected_device['hostname']}")
                return [{'device_id': selected_device_id, 'hostname': selected_device['hostname']}]
            else:
                logger.warning(f"Selected device ID {selected_device_id} not found in devices list")
    except Exception as e:
        logger.error(f"Error fetching device details: {e}")
    
    # Default fallback if anything goes wrong
    logger.info(f"Using fallback data for device ID: {selected_device_id}")
    return [{'device_id': selected_device_id, 'hostname': 'Selected Device'}] 