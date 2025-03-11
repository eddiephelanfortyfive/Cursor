import json
import os
import logging
from flask import Flask
from pathlib import Path

# Set up logging - change to WARNING level to reduce terminal output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Get the absolute path to the project root directory
# This works in both local and PythonAnywhere environments
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Load configuration
config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

# Update database path to be absolute
if not os.path.isabs(config['database_path']):
    config['database_path'] = os.path.join(PROJECT_ROOT, config['database_path'])

# Ensure the database directory exists
db_path = Path(config['database_path'])
db_dir = db_path.parent

# First, check if the directory exists
if not db_dir.exists():
    logger.warning(f"Database directory {db_dir} does not exist. Trying to create it or fallback to project directory.")
    try:
        # Try to create the directory
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created database directory {db_dir}")
    except Exception as e:
        # If we can't create the directory, fallback to project directory
        logger.warning(f"Could not create database directory: {e}")
        config['database_path'] = os.path.join(PROJECT_ROOT, "system_monitoring.db")
        logger.warning(f"Falling back to local database path: {config['database_path']}")

# Log the actual database path for debugging
logger.info(f"Using database at: {config['database_path']}")

# Initialize Flask app
flask_app = Flask(__name__)

# Import and register routes from endpoints
from api.endpoints import register_routes
register_routes(flask_app, config)  # Don't reassign flask_app

# Create and set up the Dash app
from dashboard.app import create_dash_app, set_app
dash_app = create_dash_app(server=flask_app)  # Explicitly name the parameter
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

# Only run the development server if executed directly
# This section will be ignored on PythonAnywhere which uses the WSGI file
if __name__ == '__main__':
    port = config.get('port', 5000)
    logger.info(f"Starting integrated server on port {port}")
    flask_app.run(debug=True, port=port, host='0.0.0.0') 