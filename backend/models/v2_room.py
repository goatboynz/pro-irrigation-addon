"""
Room model for v2 room-based irrigation system.

A Room represents a physical grow space with its own lighting schedule,
water events, and environmental monitoring.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Room(Base):
    """
    Room model representing a physical grow space.
    
    Attributes:
        id: Primary key
        name: Unique room name
        lights_on_entity: HA input_datetime entity for lights-on time
        lights_off_entity: HA input_datetime entity for lights-off time
        enabled: Whether the room is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        
    Relationships:
        pumps: List of pumps in this room
        water_events: List of water events for this room
        sensors: List of environmental sensors in this room
    """
    __tablename__ = "rooms_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    lights_on_entity = Column(String(255), nullable=True)
    lights_off_entity = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    pumps = relationship("PumpV2", back_populates="room", cascade="all, delete-orphan")
    water_events = relationship("WaterEvent", back_populates="room", cascade="all, delete-orphan")
    sensors = relationship("EnvironmentalSensor", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}', enabled={self.enabled})>"
