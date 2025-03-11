import dash
from dash import Input, Output,  State
from dashboard.utils.config import COLORS
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import os
import logging
import random

# Import app instance instead of creating a new one
from dashboard.app import app

# Set up logging
logging.basicConfig(level=logging.INFO)

# Get the current directory to locate config.json
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_path = os.path.join(parent_dir, 'config', 'config.json')

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Don't create a new app instance, use the imported one
# app = dash.Dash(
#     __name__, 
#     external_stylesheets=[
#         dbc.themes.BOOTSTRAP,
#         "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
#     ],
#     meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
#     prevent_initial_callbacks='initial_duplicate'  # Enable duplicate callbacks with initial call
# )

# Initialize last update timestamp
LAST_UPDATE_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Callback to automatically convert input to uppercase
@app.callback(
    Output('stock-symbol-input', 'value'),
    [Input('stock-symbol-input', 'value')],
    prevent_initial_call=True  # Don't trigger on page load
)
def convert_to_uppercase(value):
    if value is None:
        return dash.no_update
    
    # Return uppercase version of input
    return value.upper() if value else value

# Callback to update last updated time
@app.callback(
    Output('last-update-time', 'children'),
    [Input('last-update-time-store', 'data')]
)
def update_time(timestamp):
    return timestamp

# First, let's add a callback to trigger data refresh on device selection
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
    # Return a new random value to trigger the interval-dependent callbacks
    return random.randint(1, 10000)

# Helper function to create a gauge figure
def create_gauge_figure(title, value, color):
    title_text = title
    
    # If title is too long, add a line break
    if len(title) > 20:
        title_parts = title.split(' - ')
        if len(title_parts) > 1:
            title_text = f"{title_parts[0]}<br>{title_parts[1]}"
    
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title_text, 'font': {'size': 16}},
        number={'suffix': "%", 'font': {'size': 24, 'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0, 200, 0, 0.1)'},
                {'range': [50, 80], 'color': 'rgba(255, 182, 0, 0.1)'},
                {'range': [80, 100], 'color': 'rgba(255, 0, 0, 0.1)'}
            ],
        }
    )).update_layout(
        margin=dict(l=20, r=20, t=70, b=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

# Helper function to create an error gauge
def create_error_gauge(title):
    title_text = f"{title} - Error"
    
    # If title is too long, add a line break
    if len(title_text) > 20:
        title_parts = title_text.split(' - ')
        if len(title_parts) > 1:
            title_text = f"{title_parts[0]}<br>{title_parts[1]}"
    
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=0,
        title={'text': title_text, 'font': {'size': 16, 'color': COLORS['danger']}},
        number={'value': "Error", 'font': {'size': 24, 'color': COLORS['danger']}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': COLORS['danger']},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    )).update_layout(
        margin=dict(l=20, r=20, t=70, b=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

# Helper function to get color based on value
def get_color_based_on_value(value):
    if value < 50:
        return COLORS['success']
    elif value < 80:
        return COLORS['warning']
    else:
        return COLORS['danger']

# Add a clientside callback to handle page refresh when button is clicked
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks && n_clicks > 0) {
            // Force a complete page reload
            window.location.reload();
            return null;
        }
        return null;
    }
    """,
    Output('reload-trigger', 'data'),
    [Input('refresh-button', 'n_clicks')],
    prevent_initial_call=True
)

# Keep the existing callback for animation, but now it's mostly for show since we're reloading the page
@app.callback(
    [Output('refresh-icon', 'className'),
     Output('refresh-animation-store', 'data')],
    [Input('refresh-button', 'n_clicks'),
     Input('cpu-gauge', 'figure'),
     Input('ram-gauge', 'figure')],
    [State('refresh-animation-store', 'data')]
)
def animate_refresh_button(n_clicks, cpu_fig, ram_fig, animation_state):
    ctx = dash.callback_context
    
    # Check which input triggered the callback
    if not ctx.triggered:
        # No triggers yet, return default state
        return "fas fa-sync-alt me-2", {'animating': False}
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'refresh-button':
        # Button was clicked, start animation
        return "fas fa-sync-alt fa-spin me-2", {'animating': True}
    elif trigger in ['cpu-gauge', 'ram-gauge'] and animation_state.get('animating', False):
        # Data has been refreshed, stop animation
        return "fas fa-sync-alt me-2", {'animating': False}
    
    # Return current state for any other case
    return dash.no_update, dash.no_update

# Callback to populate the device selector dropdown
@app.callback(
    Output('device-selector', 'options'),
    [Input('device-update-interval', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_device_list(n_intervals, n_clicks):
    # Fetch all registered devices from the API
    try:
        response = requests.get('http://127.0.0.1:5000/devices')
        if response.status_code == 200:
            devices = response.json()
            
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
            
            return options
        else:
            # Return at least the "None" option if API call fails
            return [{'label': 'No Device Selected', 'value': 'none'}]
    except Exception as e:
        logging.error(f"Error fetching devices: {e}")
        return [{'label': 'No Device Selected', 'value': 'none'}]

# Callback to handle device selection and update the device store
@app.callback(
    [Output('device-store', 'data')],
    [Input('device-selector', 'value')]
)
def update_selected_device(selected_device_id):
    if not selected_device_id or selected_device_id == 'none':
        # No device selected or explicitly selected "none"
        return [{'device_id': None, 'hostname': 'No Device Selected'}]
    
    # Fetch the selected device details to get the hostname
    try:
        response = requests.get('http://127.0.0.1:5000/devices')
        if response.status_code == 200:
            devices = response.json()
            
            # Find the selected device
            selected_device = next((d for d in devices if d['device_id'] == selected_device_id), None)
            
            if selected_device:
                return [{'device_id': selected_device_id, 'hostname': selected_device['hostname']}]
    except Exception as e:
        logging.error(f"Error fetching device details: {e}")
    
    # Default fallback if anything goes wrong
    return [{'device_id': selected_device_id, 'hostname': 'Selected Device'}]

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)