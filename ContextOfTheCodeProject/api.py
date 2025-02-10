from flask import Flask, jsonify
from datetime import datetime, timedelta
from models import get_db_session, SystemMetrics, StockMetrics
from system_monitor import SystemMonitor
from stock_monitor import StockMonitor
import json
import os

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
system_monitor = SystemMonitor()
stock_monitor = StockMonitor()

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
    return jsonify(stock_monitor.get_current_metrics())

@app.route('/metrics/stocks/current/<symbol>')
def get_current_stock_metrics_by_symbol(symbol):
    """Get current stock metrics for a specific symbol"""
    return jsonify(stock_monitor.get_current_metrics(symbol))

@app.route('/metrics/stocks/history/<symbol>/<int:hours>')
def get_stock_metrics_history(symbol, hours):
    """Get stock metrics history for the specified symbol and hours"""
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

if __name__ == '__main__':
    app.run(
        host=config['api_server']['host'],
        port=config['api_server']['port'],
        debug=config['api_server']['debug']
    )
