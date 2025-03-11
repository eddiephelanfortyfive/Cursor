import logging
import datetime
from sqlalchemy import desc, func, create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from .schema import get_session, init_db, SystemMetric, StockData, MetricType, StockSymbol, Device, get_or_create_device


# Set logging level to WARNING to reduce terminal clutter
logging.basicConfig(level=logging.WARNING)

def init_database(db_path):
    """Initialize the database with required tables"""
    engine = create_engine(f'sqlite:///{db_path}')
    init_db(db_path)
    logging.debug(f"Database initialized at {db_path}")
    
def get_session(db_path):
    """Create and return a session for the database"""
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()

def insert_system_metric(db_path, metric_name, metric_value, device_id=None, mac_address=None):
    """Insert a system metric record into the database."""
    session = get_session(db_path)
    try:
        # Use provided device_id
        if not device_id:
            logging.error("No device_id provided for system metric")
            return False
        
        # Try to find the device first by MAC address if provided
        device = None
        if mac_address:
            device = session.query(Device).filter_by(mac_address=mac_address).first()
            # If found by MAC but device_id is different, update it
            if device and device.device_id != device_id:
                logging.warning(f"Device found by MAC {mac_address} has different device_id: {device.device_id} vs {device_id}")
                device.device_id = device_id
        
        # If not found by MAC, try to find by device_id
        if not device:
            device = session.query(Device).filter_by(device_id=device_id).first()
        
        # Only create the device if it doesn't exist
        if not device:
            # This should rarely happen since devices should be registered first
            logging.debug(f"Device {device_id} not found, creating a new one")
            device = get_or_create_device(session, device_id, mac_address=mac_address)
        
        # Get or create the metric type
        metric_type = session.query(MetricType).filter_by(name=metric_name).first()
        if not metric_type:
            metric_type = MetricType(name=metric_name)
            session.add(metric_type)
            session.flush()  # Flush to generate the ID
        
        # Create the system metric record
        metric = SystemMetric(
            metric_type_id=metric_type.id,
            device_id=device.id,
            metric_value=float(metric_value),
            timestamp=datetime.datetime.now()
        )
        session.add(metric)
        session.commit()
        logging.debug(f"Inserted system metric for device {device.hostname}: {metric_name}={metric_value}")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Error inserting system metric: {e}")
        return False
    finally:
        session.close()

def insert_stock_data(db_path, symbol, price):
    """Insert stock data record into the database."""
    session = get_session(db_path)
    try:
        # Get or create the stock symbol
        stock_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
        if not stock_symbol:
            stock_symbol = StockSymbol(symbol=symbol)
            session.add(stock_symbol)
            session.flush()  # Flush to generate the ID
        
        # Create the stock data record
        stock_data = StockData(
            symbol_id=stock_symbol.id,
            price=float(price),
            timestamp=datetime.datetime.now()
        )
        session.add(stock_data)
        session.commit()
        logging.debug(f"Inserted stock data: {symbol}={price}")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Error inserting stock data: {e}")
        return False
    finally:
        session.close()

def fetch_latest_system_metrics(db_path=None, metric_name=None, device_id=None):
    """Fetch the latest system metrics from the database, optionally filtered by metric name and device."""
    session = get_session(db_path)
    try:
        # Build the query
        query = session.query(
            MetricType.name,
            SystemMetric.metric_value,
            SystemMetric.timestamp,
            Device.device_id,
            Device.hostname
        ).join(
            MetricType,
            SystemMetric.metric_type_id == MetricType.id
        ).join(
            Device,
            SystemMetric.device_id == Device.id
        )
        
        # Apply device filter if provided
        if device_id and device_id != 'all':
            query = query.filter(Device.device_id == device_id)
            
        # Apply metric name filter if provided
        if metric_name:
            query = query.filter(MetricType.name == metric_name)
        
        # Order by timestamp desc to get the most recent
        query = query.order_by(desc(SystemMetric.timestamp))
        
        # Get latest for each metric type (for the specified device if provided)
        subq = query.subquery()
        
        results = session.query(
            subq.c.name,
            subq.c.metric_value,
            subq.c.timestamp,
            subq.c.device_id,
            subq.c.hostname
        ).all()
        
        # Format results as a dictionary
        metrics = {}
        for result in results:
            metric_name = result[0]
            metric_value = result[1]
            metrics[metric_name] = metric_value
        
        return metrics
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching latest system metrics: {e}")
        return {}
    finally:
        session.close()

def fetch_latest_stock_data(db_path, symbol):
    """Fetch the latest stock data for a specific symbol."""
    session = get_session(db_path)
    try:
        # Query with join to get the symbol name
        latest_data = session.query(
            StockSymbol.symbol,
            StockData.price,
            StockData.timestamp
        ).join(StockSymbol).filter(
            StockSymbol.symbol == symbol
        ).order_by(desc(StockData.timestamp)).first()
        
        if latest_data:
            return {
                "symbol": latest_data[0],
                "price": latest_data[1],
                "timestamp": latest_data[2].isoformat()
            }
        return None
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching latest stock data: {e}")
        return None
    finally:
        session.close()

def fetch_stock_symbols(db_path):
    """Fetch all distinct stock symbols from the database."""
    session = get_session(db_path)
    try:
        symbols = session.query(StockSymbol.symbol).all()
        return [symbol[0] for symbol in symbols]
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching stock symbols: {e}")
        return []
    finally:
        session.close()

def get_stock_history(db_path, symbol):
    """Get historical stock data for a specific symbol."""
    session = get_session(db_path)
    try:
        # Query with join to get the symbol name
        history_data = session.query(
            StockSymbol.symbol,
            StockData.price,
            StockData.timestamp
        ).join(StockSymbol).filter(
            StockSymbol.symbol == symbol
        ).order_by(StockData.timestamp.asc()).all()
        
        # Format the results
        history = [
            {
                "symbol": symbol,
                "price": price,
                "timestamp": timestamp.isoformat()
            }
            for symbol, price, timestamp in history_data
        ]
        return history
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching stock history: {e}")
        return []
    finally:
        session.close()

def get_system_metrics_history(db_path, metric_name, device_id=None):
    """Get historical metrics data for a specific metric type and device."""
    session = get_session(db_path)
    try:
        # Build the query
        query = session.query(
            MetricType.name,
            SystemMetric.metric_value,
            SystemMetric.timestamp,
            Device.device_id,
            Device.hostname
        ).join(
            MetricType,
            SystemMetric.metric_type_id == MetricType.id
        ).join(
            Device,
            SystemMetric.device_id == Device.id
        ).filter(
            MetricType.name == metric_name
        )
        
        # Apply device filter if provided
        if device_id and device_id != 'all':
            query = query.filter(Device.device_id == device_id)
        
        # Order by timestamp
        results = query.order_by(SystemMetric.timestamp.asc()).all()
        
        # Format the results
        history = []
        for result in results:
            # Ensure timestamp is not None to prevent JavaScript format errors
            timestamp_str = result[2].isoformat() if result[2] else ""
            
            history.append({
                "metric_name": result[0],
                "metric_value": result[1],
                "timestamp": timestamp_str,
                "device_id": result[3],
                "device_hostname": result[4] or "Unknown Device"
            })
        
        return history
    except SQLAlchemyError as e:
        logging.error(f"Database error fetching system metrics history: {e}")
        return []
    finally:
        session.close()