from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship
import datetime
import socket
import uuid
import os

Base = declarative_base()

# Device table to track different systems/devices
class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False, unique=True)  # Unique identifier for the device
    hostname = Column(String, nullable=False)
    os_info = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)
    
    # Relationship - one device can have many system metrics
    metrics = relationship("SystemMetric", back_populates="device")
    
    def __repr__(self):
        return f"<Device(device_id='{self.device_id}', hostname='{self.hostname}')>"
    
    def to_dict(self):
        return {
            "device_id": self.device_id,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "last_seen": self.last_seen.isoformat()
        }

# Metric types table
class MetricType(Base):
    __tablename__ = 'metric_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationship - one metric type can have many system metrics
    metrics = relationship("SystemMetric", back_populates="metric_type")
    
    def __repr__(self):
        return f"<MetricType(name='{self.name}')>"

# System metrics table
class SystemMetric(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_type_id = Column(Integer, ForeignKey('metric_types.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    
    # Relationship - many system metrics belong to one metric type
    metric_type = relationship("MetricType", back_populates="metrics")
    
    # Relationship - many system metrics belong to one device
    device = relationship("Device", back_populates="metrics")
    
    def __repr__(self):
        return f"<SystemMetric(device='{self.device.hostname if self.device else None}', metric_type='{self.metric_type.name if self.metric_type else None}', value={self.metric_value})>"
    
    def to_dict(self):
        return {
            "device_id": self.device.device_id if self.device else None,
            "device_hostname": self.device.hostname if self.device else None,
            "metric_name": self.metric_type.name if self.metric_type else None,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat()
        }

# Stock symbols table
class StockSymbol(Base):
    __tablename__ = 'stock_symbols'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, unique=True)
    
    # Relationship - one stock symbol can have many stock data points
    data_points = relationship("StockData", back_populates="symbol_info")
    
    def __repr__(self):
        return f"<StockSymbol(symbol='{self.symbol}')>"

# Stock data table
class StockData(Base):
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.id'), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    
    # Relationship - many stock data points belong to one stock symbol
    symbol_info = relationship("StockSymbol", back_populates="data_points")
    
    def __repr__(self):
        return f"<StockData(symbol='{self.symbol_info.symbol if self.symbol_info else None}', price={self.price})>"
    
    def to_dict(self):
        return {
            "symbol": self.symbol_info.symbol if self.symbol_info else None,
            "price": self.price,
            "timestamp": self.timestamp.isoformat()
        }

# Helper function to get or create a device based on device_id
def get_or_create_device(session, device_id=None, hostname=None, os_info=None):
    # If no device_id provided, generate a UUID as fallback
    if not device_id:
        # Create a UUID as fallback if no device ID is provided
        device_id = str(uuid.uuid4())
    
    # If no hostname provided, use the current machine's hostname
    if not hostname:
        hostname = socket.gethostname()
    
    # If no OS info provided, try to get it
    if not os_info:
        try:
            os_info = os.uname().sysname + " " + os.uname().release
        except:
            # Fallback for Windows
            os_info = os.name
    
    # Find existing device or create a new one
    device = session.query(Device).filter_by(device_id=device_id).first()
    
    if not device:
        # Create new device
        device = Device(
            device_id=device_id,
            hostname=hostname,
            os_info=os_info
        )
        session.add(device)
        session.commit()
    else:
        # Update last seen timestamp
        device.last_seen = datetime.datetime.now()
        device.hostname = hostname  # Update hostname in case it changed
        device.os_info = os_info    # Update OS info in case it changed
        session.commit()
    
    return device

# Database connection handling
def get_engine(db_path):
    return create_engine(f'sqlite:///{db_path}')

def init_db(db_path):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    
    # Initialize the session
    session = get_session(db_path)
    
    # Add default metric types if they don't exist
    default_metrics = ["cpu_usage", "ram_usage"]
    for metric_name in default_metrics:
        if not session.query(MetricType).filter_by(name=metric_name).first():
            session.add(MetricType(name=metric_name))
    
    session.commit()
    session.close()
    
    return engine

def get_session(db_path):
    engine = get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory) 