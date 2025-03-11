#!/usr/bin/env python3
"""
Migration script to add the mac_address column to the devices table
and populate it with placeholder values for existing devices.
"""

import os
import sys
import logging
import json
from pathlib import Path
from sqlalchemy import create_engine, Column, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Load configuration
config_path = PROJECT_ROOT / 'config' / 'config.json'
with open(config_path) as config_file:
    config = json.load(config_file)

# Update database path to be absolute
if not os.path.isabs(config['database_path']):
    DATABASE_PATH = os.path.join(str(PROJECT_ROOT), config['database_path'])
else:
    DATABASE_PATH = config['database_path']

# Create database engine
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Session = sessionmaker(bind=engine)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        conn = engine.connect()
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        conn.close()
        return column_name in columns
    except Exception as e:
        logger.error(f"Error checking if column exists: {e}")
        return False

def add_mac_address_column():
    """Add the mac_address column to the devices table"""
    try:
        # Check if the column already exists
        if check_column_exists('devices', 'mac_address'):
            logger.info("MAC address column already exists, skipping creation")
            return True
        
        # Add the column
        conn = engine.connect()
        # SQLite doesn't support adding a NOT NULL column with no default to an existing table
        # So we add it as nullable first
        conn.execute(text("ALTER TABLE devices ADD COLUMN mac_address VARCHAR"))
        logger.info("Added mac_address column to devices table")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding mac_address column: {e}")
        return False

def populate_mac_addresses():
    """Populate MAC addresses for existing devices"""
    session = Session()
    try:
        # Import the Device model (done here to avoid circular imports)
        from database.schema import Device
        
        # Get all devices
        devices = session.query(Device).all()
        logger.info(f"Found {len(devices)} devices to update")
        
        # Update each device with a placeholder MAC address based on its device_id
        for device in devices:
            if not device.mac_address:
                # Generate a placeholder MAC address from the device_id
                placeholder_mac = f"auto-{device.device_id[:12]}"
                device.mac_address = placeholder_mac
                logger.info(f"Set placeholder MAC {placeholder_mac} for device {device.device_id}")
        
        # Commit the changes
        session.commit()
        logger.info("Successfully populated MAC addresses")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error populating MAC addresses: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error populating MAC addresses: {e}")
        return False
    finally:
        session.close()

def set_unique_constraint():
    """Set unique constraint on mac_address column"""
    # Note: SQLite doesn't support adding constraints to existing tables directly.
    # In a real-world application, you would:
    # 1. Create a new table with the desired structure
    # 2. Copy data from the old table
    # 3. Drop the old table
    # 4. Rename the new table
    
    # For this demo, we'll just check for duplicate MAC addresses and make them unique
    session = Session()
    try:
        # Import the Device model
        from database.schema import Device
        
        # Get all devices
        devices = session.query(Device).all()
        
        # Track seen MAC addresses
        seen_macs = {}
        
        # Check for duplicates and make them unique
        for device in devices:
            if device.mac_address in seen_macs:
                # Make it unique by appending the device ID
                new_mac = f"{device.mac_address}-{device.id}"
                logger.info(f"Changing duplicate MAC {device.mac_address} to {new_mac}")
                device.mac_address = new_mac
            else:
                seen_macs[device.mac_address] = True
        
        # Commit the changes
        session.commit()
        logger.info("Successfully ensured all MAC addresses are unique")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error ensuring unique MAC addresses: {e}")
        return False
    finally:
        session.close()

def main():
    """Run the migration"""
    logger.info(f"Starting migration for database at {DATABASE_PATH}")
    
    # Add the MAC address column
    if not add_mac_address_column():
        logger.error("Failed to add MAC address column, aborting")
        return False
    
    # Populate MAC addresses for existing devices
    if not populate_mac_addresses():
        logger.error("Failed to populate MAC addresses, aborting")
        return False
    
    # Ensure MAC addresses are unique
    if not set_unique_constraint():
        logger.error("Failed to set unique constraint, aborting")
        return False
    
    logger.info("Migration completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 