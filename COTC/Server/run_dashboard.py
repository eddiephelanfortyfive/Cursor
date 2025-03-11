import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dashboard.app import app
from dashboard.layouts.main_layout import create_layout

# Set the app layout
logger.info("Setting application layout")
app.layout = create_layout()

# Import all callback modules after setting layout
logger.info("Importing callback modules")
from dashboard.callbacks import device_callbacks, system_metrics_callbacks, history_callbacks, page_callbacks

# Explicitly set suppress_callback_exceptions
app.config.suppress_callback_exceptions = True

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DASHBOARD_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting dashboard server on port {port} with debug={debug}")
    app.run_server(debug=debug, host='0.0.0.0', port=port)