import psutil
import time
from datetime import datetime
from models import SystemMetrics, get_db_session
import logging
import json
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
logger = logging.getLogger('system_monitor')

class SystemMonitor:
    @staticmethod
    def collect_metrics():
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage_percent=psutil.disk_usage('/').percent,
                network_bytes_sent=psutil.net_io_counters().bytes_sent,
                network_bytes_recv=psutil.net_io_counters().bytes_recv
            )
            
            session = get_db_session()
            try:
                session.add(metrics)
                session.commit()
                logger.info("System metrics collected successfully")
            except Exception as e:
                session.rollback()
                logger.error(f"Database error: {str(e)}")
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            
    @staticmethod
    def get_current_metrics():
        """Get the latest system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict()
        }
