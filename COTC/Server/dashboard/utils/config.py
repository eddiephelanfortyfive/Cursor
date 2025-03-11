import os
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

API_HOST = "127.0.0.1"
API_PORT = int(os.environ.get('API_PORT', 5000))
API_BASE_URL = "http://127.0.0.1:5000"


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.json'
    
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading configuration: {e}")
        # Return default configuration
        return {
            "system_metrics": ["cpu_usage", "ram_usage"],
            "database_path": "system_monitoring.db"
        }

# Load configuration on module import
CONFIG = load_config()

# Define colors for UI elements
COLORS = {
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'primary': '#007bff',
    'secondary': '#6c757d',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'white': '#ffffff',
}

# Common styles
CARD_STYLE = {
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'marginBottom': '20px',
    'borderRadius': '8px',
    'padding': '15px',
    'background': COLORS['white']
}

BUTTON_STYLE = {
    'margin-right': '10px',
    'margin-bottom': '10px',
    'border-radius': '4px',
}

# Updated TABLE_STYLE with all necessary properties
TABLE_STYLE = {
    'table': {
        'overflowX': 'auto',
        'border': '1px solid #e0e0e0',
        'borderRadius': '5px'
    },
    'cell': {
        'textAlign': 'left',
        'padding': '8px',
        'fontFamily': 'Arial, sans-serif'
    },
    'header': {
        'fontWeight': 'bold',
        'backgroundColor': '#f8f9fa',
        'borderBottom': '1px solid #dee2e6'
    },
    'data': {
        'backgroundColor': COLORS['white']
    },
    'conditional': [
        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
    ]
} 