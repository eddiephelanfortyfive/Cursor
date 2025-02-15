from apscheduler.schedulers.background import BackgroundScheduler
from system_monitor import SystemMonitor
from stock_monitor import StockMonitor
from models import init_db
from api import app
import json
import logging
import os

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Configure logging
logging.basicConfig(
    level=config['logging']['level'],
    format=config['logging']['format'],
    filename=config['logging']['file']
)
logger = logging.getLogger('main')

def main():
    # Initialize database
    print('Initializing database...')
    init_db()
    
    # Create monitors
    print('Creating monitors...')
    system_monitor = SystemMonitor()
    stock_monitor = StockMonitor()
    
    # Test Finnhub connection
    print('Testing Finnhub connection...')
    stock_monitor.test_finnhub_connection()

    # Create scheduler
    print('Creating scheduler...')
    scheduler = BackgroundScheduler()
    
    # Add jobs
    print('Adding jobs...')
    scheduler.add_job(
        system_monitor.collect_metrics,
        'interval',
        seconds=config['monitoring']['system_metrics_interval']
    )
    
    # Schedule stock metrics collection every minute
    scheduler.add_job(
        stock_monitor.collect_metrics,
        'interval',
        seconds=60  # Run every minute
    )
    
    # Start scheduler
    print('Starting scheduler...')
    scheduler.start()
    
    # Start Flask API
    print('Starting Flask API...')
    app.run(
        host=config['api_server']['host'],
        port=config['api_server']['port'],
        debug=config['api_server']['debug']
    )
    print('Flask API started.')

if __name__ == '__main__':
    main()
