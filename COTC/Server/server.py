import json
import os
import logging
from flask import Flask

# Set up logging - change to WARNING level to reduce terminal output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Import the Flask API app
from api.endpoints import app as flask_app

# Create a Dash app instance using the Flask server
import dash
import dash_bootstrap_components as dbc
from datetime import datetime

# Import the dashboard app module
from dashboard.app import set_app

def create_dash_app(server):
    """Create and configure the Dash application with an existing Flask server"""
    app = dash.Dash(
        __name__, 
        server=server,  # Use the existing Flask server
        url_base_pathname='/dashboard/',  # Mount the dashboard at /dashboard/
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
        ],
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        prevent_initial_callbacks='initial_duplicate'  # Enable duplicate callbacks with initial call
    )
    
    # Add custom CSS for dropdown menus
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>System Monitoring Dashboard</title>
            {%favicon%}
            {%css%}
            <style>
                /* Ensure dropdown menus are fully visible */
                .dash-dropdown .Select-menu-outer {
                    display: block !important;
                    position: absolute !important;
                    z-index: 10 !important;
                }
                
                /* Device selector specific styling */
                #device-selector .Select-menu-outer {
                    min-width: 300px;
                    overflow-y: auto;
                    max-height: 400px !important;
                }
                
                /* Style for dropdown option text */
                .dash-dropdown .Select-option {
                    white-space: normal;
                    word-break: break-word;
                    padding: 8px 10px;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Make sure exceptions are propagated to our debugging tools
    app.config.suppress_callback_exceptions = True
    
    return app

# Create the Dash app using the Flask server
dash_app = create_dash_app(flask_app)

# Set the app instance in the dashboard module
set_app(dash_app)

# Configure the Dash app's layout
from dashboard.layouts.main_layout import create_layout
dash_app.layout = create_layout()

# Import all Dash callback modules after setting layout
from dashboard.callbacks import device_callbacks, system_metrics_callbacks, history_callbacks, page_callbacks, stock_callbacks

# Add a redirection route for the root URL to the dashboard
@flask_app.route('/')
def index():
    return flask_app.redirect('/dashboard/')

if __name__ == '__main__':
    # Load configuration
    with open('config/config.json', 'r') as config_file:
        config = json.load(config_file)
    port = config.get('port', 5000)

    logger.info(f"Starting integrated server on port {port}")
    flask_app.run(debug=True, port=port, host='0.0.0.0') 