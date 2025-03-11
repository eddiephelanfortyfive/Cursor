import dash
from dash.dependencies import Input, Output, State
from dash import html, dash_table
import logging
import requests
import datetime
from dashboard.app import app, LAST_UPDATE_TIME
from dashboard.components.charts import create_gauge_figure, create_error_gauge, get_color_based_on_value
from dashboard.utils.config import API_BASE_URL

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Change from INFO to WARNING

# Global variable for last update time
LAST_UPDATE_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Callback to update CPU and RAM gauges
@app.callback(
    [Output('cpu-gauge', 'figure'),
     Output('ram-gauge', 'figure'),
     Output('last-update-time-store', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks'),
     Input('device-store', 'data')],  # Added device-store as direct input
)
def update_system_metrics(n_intervals, n_clicks, device_data):
    """Update the CPU and RAM gauges with current system metrics"""
    global LAST_UPDATE_TIME
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'no trigger'
    
    logger.info(f"update_system_metrics triggered by {trigger}, interval: {n_intervals}, device: {device_data}")
    
    # Get the device ID if available
    device_id = None
    if device_data and isinstance(device_data, dict):
        device_id = device_data.get('device_id')
    
    # If no device is selected, show error gauges
    if not device_id:
        logger.warning("No device selected, returning error gauges")
        cpu_figure = create_error_gauge("CPU Usage")
        ram_figure = create_error_gauge("RAM Usage")
        return cpu_figure, ram_figure, LAST_UPDATE_TIME
    
    # Fetch metrics from API
    try:
        api_url = f"{API_BASE_URL}/metrics/system/latest?device_id={device_id}"
        logger.info(f"Fetching metrics from: {api_url}")
        
        response = requests.get(api_url)
        logger.info(f"Metrics API response status: {response.status_code}")
        
        if response.status_code == 200:
            metrics_data = response.json()
            logger.info(f"Retrieved metrics type: {type(metrics_data)}, data: {metrics_data}")
            
            # Handle both list and dictionary responses
            if isinstance(metrics_data, list):
                # Find the CPU and RAM metrics in the list
                cpu_metric = next((m for m in metrics_data if m.get('metric_name') == 'cpu_usage'), None)
                ram_metric = next((m for m in metrics_data if m.get('metric_name') == 'ram_usage'), None)
                
                cpu_value = cpu_metric.get('metric_value', 0) if cpu_metric else 0
                ram_value = ram_metric.get('metric_value', 0) if ram_metric else 0
            else:
                # Handle dictionary response
                cpu_value = metrics_data.get('cpu_usage', 0)
                ram_value = metrics_data.get('ram_usage', 0)
            
            # Create CPU gauge
            cpu_color = get_color_based_on_value(cpu_value)
            cpu_figure = create_gauge_figure("CPU Usage", cpu_value, cpu_color)
            
            # Create RAM gauge
            ram_color = get_color_based_on_value(ram_value)
            ram_figure = create_gauge_figure("RAM Usage", ram_value, ram_color)
            
            # Update last update time
            LAST_UPDATE_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Updated gauges. CPU: {cpu_value}%, RAM: {ram_value}%")
            
            return cpu_figure, ram_figure, LAST_UPDATE_TIME
        else:
            logger.error(f"Error fetching metrics: {response.status_code}, response: {response.text}")
    except Exception as e:
        logger.error(f"Exception fetching metrics: {e}")
    
    # Return error state if something went wrong
    logger.warning("Returning error gauges due to API error")
    cpu_figure = create_error_gauge("CPU Usage")
    ram_figure = create_error_gauge("RAM Usage")
    return cpu_figure, ram_figure, LAST_UPDATE_TIME

# Callback to update the last update time display
@app.callback(
    Output('last-update-time', 'children'),
    [Input('last-update-time-store', 'data')]
)
def update_time(timestamp):
    """Update the last update time display"""
    return f"Last Updated: {timestamp}" 