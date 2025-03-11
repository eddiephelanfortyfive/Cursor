import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash import html, dcc
import logging
import datetime
import json
import os
from pathlib import Path
from dashboard.app import app, LAST_UPDATE_TIME
from database.models import get_session
from database.schema import Device

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Change from INFO to WARNING

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

# Callback to check database connectivity
@app.callback(
    Output('interval-component', 'disabled'),
    Input('device-update-interval', 'n_intervals')
)
def check_database_connectivity(n_intervals):
    """Check if the database is accessible"""
    logger.info("Checking database connectivity")
    try:
        session = get_session(DATABASE_PATH)
        # Try a simple query
        session.query(Device).first()
        session.close()
        logger.info("Database connection successful")
        return False  # Enable the interval
    except Exception as e:
        logger.error(f"Database connection error: {e}")
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