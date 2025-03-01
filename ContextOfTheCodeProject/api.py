from flask import Flask, jsonify, render_template
from datetime import datetime, timedelta
from models import get_db_session, SystemMetrics, StockMetrics
from system_monitor import SystemMonitor
from stock_monitor import StockMonitor
import json
import os
import logging
import sqlite3

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
system_monitor = SystemMonitor()
stock_monitor = StockMonitor()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def get_db_connection():
    conn = sqlite3.connect('monitoring.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/metrics/system/current')
def get_current_system_metrics():
    """Get current system metrics"""
    return jsonify(system_monitor.get_current_metrics())

@app.route('/metrics/system/history/<int:hours>')
def get_system_metrics_history(hours):
    """Get system metrics history for the specified hours"""
    session = get_db_session()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        metrics = session.query(SystemMetrics)\
            .filter(SystemMetrics.timestamp >= since)\
            .all()
        
        return jsonify([{
            'timestamp': m.timestamp.isoformat(),
            'cpu_percent': m.cpu_percent,
            'memory_percent': m.memory_percent,
            'disk_usage_percent': m.disk_usage_percent,
            'network_bytes_sent': m.network_bytes_sent,
            'network_bytes_recv': m.network_bytes_recv
        } for m in metrics])
    finally:
        session.close()

@app.route('/metrics/stocks/current')
def get_current_stock_metrics():
    """Get current stock metrics"""
    current_metrics = {}
    for symbol in stock_monitor.symbols:
        try:
            quote = stock_monitor.client.quote(symbol)
            current_metrics[symbol] = {
                'price': quote['c'],
                'high': quote['h'],
                'low': quote['l'],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting current stock metrics for {symbol}: {str(e)}")
    return jsonify(current_metrics)

@app.route('/metrics/stocks/current/<symbol>')
def get_current_stock_metrics_by_symbol(symbol):
    """Get current stock metrics for a specific symbol"""
    return jsonify(stock_monitor.get_current_metrics(symbol))

@app.route('/metrics/stocks/history/<symbol>/<int:hours>')
def get_stock_metrics_history(symbol, hours):
    """Get stock metrics history for the specified symbol and hours"""
    logger.info(f"Fetching stock history for {symbol} over the last {hours} hours")
    session = get_db_session()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        metrics = session.query(StockMetrics)\
            .filter(StockMetrics.symbol == symbol)\
            .filter(StockMetrics.timestamp >= since)\
            .all()
        
        return jsonify([{
            'timestamp': m.timestamp.isoformat(),
            'symbol': m.symbol,
            'price': m.price,
            'high': m.high,
            'low': m.low,
            'volume': m.volume
        } for m in metrics])
    finally:
        session.close()

@app.route('/metrics/stocks/history/<symbol>', methods=['GET'])
def get_stock_history(symbol):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, price FROM stock_metrics WHERE symbol = ? ORDER BY timestamp', (symbol,))
    rows = cursor.fetchall()
    conn.close()
    
    data = [{'timestamp': row['timestamp'], 'price': row['price']} for row in rows]
    
    # Log the data being returned
    logger.debug(f"Data for {symbol}: {data}")
    
    return jsonify(data)

@app.route('/metrics/stocks/symbols', methods=['GET'])
def get_configured_stock_symbols():
    """Get stock symbols from config.json"""
    symbols = config['api']['stocks_to_monitor']
    logger.debug(f"Configured stock symbols: {symbols}")
    return jsonify(symbols)

if __name__ == '__main__':
    app.run(
        host=config['api_server']['host'],
        port=config['api_server']['port'],
        debug=config['api_server']['debug']
    )
