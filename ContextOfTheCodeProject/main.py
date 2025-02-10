from apscheduler.schedulers.background import BackgroundScheduler
from system_monitor import SystemMonitor
from stock_monitor import StockMonitor
from models import init_db
from api import app
import json
import logging

# Load configuration
with open('config.json', 'r') as f:
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
    init_db()
    
    # Create monitors
    system_monitor = SystemMonitor()
    stock_monitor = StockMonitor()
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add jobs
    scheduler.add_job(
        system_monitor.collect_metrics,
        'interval',
        seconds=config['monitoring']['system_metrics_interval']
    )
    
    scheduler.add_job(
        stock_monitor.collect_metrics,
        'interval',
        seconds=config['monitoring']['stock_metrics_interval']
    )
    
    # Start scheduler
    scheduler.start()
    
    # Start Flask API
    app.run(
        host=config['api_server']['host'],
        port=config['api_server']['port'],
        debug=config['api_server']['debug']
    )

if __name__ == '__main__':
    main()
