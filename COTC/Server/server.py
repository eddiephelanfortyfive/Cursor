import json
import os
import logging
from flask import Flask
from pathlib import Path

# Set up logging - change to WARNING level to reduce terminal output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Get the absolute path to the project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()

# Load configuration
config_path = PROJECT_ROOT / 'config' / 'config.json'
with open(config_path) as config_file:
    config = json.load(config_file)

# Update database path to be absolute
if not os.path.isabs(config['database_path']):
    config['database_path'] = str(PROJECT_ROOT / config['database_path'])

# Initialize Flask app
flask_app = Flask(__name__)

# Import and register routes from endpoints
from api.endpoints import register_routes
flask_app = register_routes(flask_app, config)

# Create and set up the Dash app
from dashboard.app import create_dash_app, set_app
dash_app = create_dash_app(flask_app)
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
    port = config.get('port', 5000)
    logger.info(f"Starting integrated server on port {port}")
    flask_app.run(debug=True, port=port, host='0.0.0.0') 