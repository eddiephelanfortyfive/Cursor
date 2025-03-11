import dash
from dash.dependencies import Input, Output, State
from dash import html
import logging
import datetime
import json
import os
from pathlib import Path
from dashboard.app import app
from dashboard.components.charts import create_gauge_figure, create_error_gauge, get_color_based_on_value
from database.models import fetch_latest_system_metrics

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

# Callback to update CPU and RAM gauges
@app.callback(
    [Output('cpu-gauge', 'figure'),
     Output('ram-gauge', 'figure'),
     Output('last-update-time-store', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks'),
     Input('device-store', 'data')],
)
def update_system_metrics(n_intervals, n_clicks, device_data):
    """Update the CPU and RAM gauges with current system metrics"""
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'no trigger'
    
    logger.warning(f"update_system_metrics triggered by {trigger}")
    logger.warning(f"Device data: {device_data}")
    
    # Get the device ID if available
    device_id = device_data.get('device_id') if device_data else None
    
    # If no device is selected, show error gauges
    if not device_id:
        logger.warning("No device selected, returning error gauges")
        cpu_figure = create_error_gauge("CPU Usage - No Device")
        ram_figure = create_error_gauge("RAM Usage - No Device")
        return cpu_figure, ram_figure, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fetch metrics from database
    try:
        logger.warning(f"Fetching metrics for device {device_id}")
        metrics = fetch_latest_system_metrics(db_path=DATABASE_PATH, device_id=device_id)
        logger.warning(f"Retrieved metrics: {metrics}")
        
        if not metrics:
            logger.warning("No metrics found for device")
            cpu_figure = create_error_gauge("CPU Usage - No Data")
            ram_figure = create_error_gauge("RAM Usage - No Data")
            return cpu_figure, ram_figure, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract CPU and RAM values
        cpu_value = metrics.get('cpu_usage', 0)
        ram_value = metrics.get('ram_usage', 0)
        
        logger.warning(f"CPU Usage: {cpu_value}%, RAM Usage: {ram_value}%")
        
        # Create CPU gauge
        cpu_color = get_color_based_on_value(cpu_value)
        cpu_figure = create_gauge_figure("CPU Usage", cpu_value, cpu_color)
        
        # Create RAM gauge
        ram_color = get_color_based_on_value(ram_value)
        ram_figure = create_gauge_figure("RAM Usage", ram_value, ram_color)
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cpu_figure, ram_figure, current_time
        
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")
        cpu_figure = create_error_gauge("CPU Usage - Error")
        ram_figure = create_error_gauge("RAM Usage - Error")
        return cpu_figure, ram_figure, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Callback to update the last update time display
@app.callback(
    Output('last-update-time', 'children'),
    [Input('last-update-time-store', 'data')]
)
def update_time(timestamp):
    """Update the last update time display"""
    return f"Last Updated: {timestamp}" 