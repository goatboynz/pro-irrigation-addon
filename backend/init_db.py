"""
Database initialization script for v2 room-based irrigation system.

This script:
1. Creates all database tables
2. Initializes default SystemSettings row
"""

from models.database import engine, SessionLocal, create_tables
from models.v2_settings import SystemSettings


def init_database():
    """
    Initialize the database with tables and default data.
    
    This function:
    - Creates all tables defined in the models
    - Adds a default SystemSettings row (id=1) if it doesn't exist
    
    Safe to call multiple times - will not duplicate data.
    """
    print("Initializing database...")
    
    # Create all tables
    print("Creating database tables...")
    create_tables()
    print("✓ Tables created successfully")
    
    # Initialize default SystemSettings
    print("Checking SystemSettings...")
    db = SessionLocal()
    try:
        # Check if SystemSettings already exists
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        
        if settings is None:
            # Create default settings
            default_settings = SystemSettings(
                id=1,
                pump_startup_delay_seconds=5,
                zone_switch_delay_seconds=2,
                scheduler_interval_seconds=60
            )
            db.add(default_settings)
            db.commit()
            print("✓ Default SystemSettings created")
        else:
            print("✓ SystemSettings already exists")
    except Exception as e:
        print(f"✗ Error initializing SystemSettings: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("Database initialization complete!")


if __name__ == "__main__":
    init_database()
