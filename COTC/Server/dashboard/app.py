import dash
import dash_bootstrap_components as dbc
from datetime import datetime

# Initialize app-level variables
LAST_UPDATE_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_dash_app(server=None):
    """Create and configure the Dash application"""
    app = dash.Dash(
        __name__, 
        server=server,  # Use the provided Flask server if available
        url_base_pathname='/dashboard/' if server else '/',
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

# This app instance will be replaced by the one from server.py
# Keeping this for compatibility with existing modules
app = None

# When this module is imported from server.py, update this variable
def set_app(dash_app):
    global app
    app = dash_app 