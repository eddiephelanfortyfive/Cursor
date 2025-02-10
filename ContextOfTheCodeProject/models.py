from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import os

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Create database engine
engine = create_engine(config['database']['connection_string'])
Session = sessionmaker(bind=engine)
Base = declarative_base()

class SystemMetrics(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_usage_percent = Column(Float)
    network_bytes_sent = Column(Integer)
    network_bytes_recv = Column(Integer)

class StockMetrics(Base):
    __tablename__ = 'stock_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(10))
    price = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Integer)

def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(engine)

def get_db_session():
    """Get a new database session"""
    return Session()
