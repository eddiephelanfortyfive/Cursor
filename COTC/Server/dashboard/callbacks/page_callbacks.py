import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash import html, dcc
import logging
import datetime
import requests
from dashboard.app import app, LAST_UPDATE_TIME
from dashboard.utils.config import API_BASE_URL
import time

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Change from INFO to WARNING

# Callback to update UI refresh animation
@app.callback(
    [
        Output('refresh-spinner', 'className'),
        Output('refresh-button', 'disabled')
    ],
    [
        Input('refresh-button', 'n_clicks'),
    ],
    [
        State('refresh-spinner', 'className')
    ],
    prevent_initial_call=True
)
def update_refresh_ui(n_clicks, current_class):
    """Update refresh button UI animation"""
    if n_clicks:
        # Start spinning animation
        return "fas fa-sync-alt fa-spin", True
    
    # Default (non-spinning)
    return "fas fa-sync-alt", False

# Callback to check API connectivity
@app.callback(
    Output('interval-component', 'disabled'),
    Input('device-update-interval', 'n_intervals')
)
def check_api_connectivity(n_intervals):
    """Check if the API is reachable and log the result"""
    logger.info(f"Checking API connectivity to {API_BASE_URL}")
    try:
        response = requests.get(f"{API_BASE_URL}/devices")
        if response.status_code == 200:
            logger.info("API connection successful")
            return False  # Enable the interval
        else:
            logger.error(f"API connection failed with status {response.status_code}")
            return True  # Disable the interval
    except Exception as e:
        logger.error(f"API connection error: {e}")
        return True  # Disable the interval

# Client-side JavaScript function for page refresh
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            window.location.reload();
            return Math.random();
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('reload-trigger', 'data'),
    Input('refresh-button', 'n_clicks'),
    prevent_initial_call=True
)