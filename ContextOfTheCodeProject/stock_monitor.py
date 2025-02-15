import finnhub
import time
from datetime import datetime
from models import StockMetrics, get_db_session
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
logger = logging.getLogger('stock_monitor')

class StockMonitor:
    def __init__(self):
        self.client = finnhub.Client(api_key=config['api']['finnhub_key'])
        self.symbols = config['api']['stocks_to_monitor']

    def collect_metrics(self):
        """Collect current stock prices for all configured stocks"""
        for symbol in self.symbols:
            try:
                quote = self.client.quote(symbol)
                # Remove or comment out the following line to stop logging the API response
                # logger.debug(f"API response for {symbol}: {json.dumps(quote, indent=2)}")
                metrics = StockMetrics(
                    symbol=symbol,
                    price=quote['c'],  # Current price
                    high=quote['h'],   # High price of the day
                    low=quote['l'],    # Low price of the day
                )

                session = get_db_session()
                try:
                    session.add(metrics)
                    session.commit()
                    logger.info(f"Stock metrics collected successfully for {symbol}")
                except Exception as e:
                    session.rollback()
                    logger.error(f"Database error for {symbol}: {str(e)}")
                finally:
                    session.close()

            except Exception as e:
                logger.error(f"Error collecting stock metrics for {symbol}: {str(e)}")

    def get_current_metrics(self, symbol=None):
        """Get the latest stock metrics"""
        try:
            if symbol:
                quote = self.client.quote(symbol)
                return {symbol: quote}
            else:
                return {sym: self.client.quote(sym) for sym in self.symbols}
        except Exception as e:
            logger.error(f"Error getting current stock metrics: {str(e)}")
            return None

    def test_finnhub_connection(self):
        """Test the connection to Finnhub API"""
        try:
            quote = self.client.quote('AAPL')  # Test with a known stock symbol
            print("Finnhub connection successful:", quote)
        except Exception as e:
            print("Finnhub connection failed:", str(e))
