"""Database configuration and session management."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

# Database path - use /data directory for Home Assistant add-on persistence
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/irrigation.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for SQL query logging
)

# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This function should be called on application startup.
    It will create all tables defined in the models if they don't exist.
    """
    # Import all models to ensure they are registered with Base
    from .pump import Pump
    from .zone import Zone
    from .global_settings import GlobalSettings
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def check_db_health() -> bool:
    """
    Check database health by attempting a simple query.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        db = SessionLocal()
        # Execute a simple query to check connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False
