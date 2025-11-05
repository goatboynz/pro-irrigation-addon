"""
System Settings model for v2 room-based irrigation system.

Singleton table for system-wide configuration.
"""

from sqlalchemy import Column, Integer, DateTime, CheckConstraint
from sqlalchemy.sql import func
from .database import Base


class SystemSettings(Base):
    """
    System Settings model for global configuration.
    
    This is a singleton table (only one row allowed).
    
    Attributes:
        id: Primary key (always 1)
        pump_startup_delay_seconds: Delay before opening zone after pump starts
        zone_switch_delay_seconds: Delay between closing one zone and opening next
        scheduler_interval_seconds: How often scheduler checks for events
        updated_at: Timestamp of last update
    """
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    pump_startup_delay_seconds = Column(Integer, default=5, nullable=False)
    zone_switch_delay_seconds = Column(Integer, default=2, nullable=False)
    scheduler_interval_seconds = Column(Integer, default=60, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraint to ensure only one row
    __table_args__ = (
        CheckConstraint('id = 1', name='singleton_check'),
    )
    
    def __repr__(self):
        return f"<SystemSettings(pump_delay={self.pump_startup_delay_seconds}s, zone_delay={self.zone_switch_delay_seconds}s)>"
