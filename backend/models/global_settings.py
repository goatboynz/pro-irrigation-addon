"""Global settings model for irrigation system."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from .database import Base


class GlobalSettings(Base):
    """
    Global settings model for system-wide configuration.
    
    Stores references to Home Assistant entities that provide timing parameters
    for auto mode scheduling. Only one row should exist in this table.
    """
    
    __tablename__ = "global_settings"
    
    id = Column(Integer, primary_key=True)
    
    # Entity references for timing parameters
    lights_on_entity = Column(String(255), nullable=True)
    lights_off_entity = Column(String(255), nullable=True)
    p1_delay_entity = Column(String(255), nullable=True)
    p2_delay_entity = Column(String(255), nullable=True)
    p2_buffer_entity = Column(String(255), nullable=True)
    
    # Feed schedule notes
    feed_notes = Column(Text, nullable=True)
    
    # Timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<GlobalSettings(id={self.id})>"
