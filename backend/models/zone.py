"""Zone model for irrigation system."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Zone(Base):
    """
    Zone model representing an irrigation zone controlled by a switch entity.
    
    A zone belongs to a pump and can operate in either auto or manual mode.
    Auto mode uses global settings to calculate schedules, while manual mode
    uses user-specified times.
    """
    
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    pump_id = Column(Integer, ForeignKey("pumps.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    switch_entity = Column(String(255), nullable=False)
    mode = Column(String(20), nullable=False)  # 'auto' or 'manual'
    
    # Auto mode fields
    p1_duration_sec = Column(Integer, nullable=True)
    p2_event_count = Column(Integer, nullable=True)
    p2_duration_sec = Column(Integer, nullable=True)
    
    # Manual mode fields - stored as text (JSON array of times)
    p1_manual_list = Column(Text, nullable=True)
    p2_manual_list = Column(Text, nullable=True)
    
    # Zone status
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to pump
    pump = relationship("Pump", back_populates="zones")
    
    def __repr__(self) -> str:
        return f"<Zone(id={self.id}, name='{self.name}', pump_id={self.pump_id}, mode='{self.mode}', enabled={self.enabled})>"
