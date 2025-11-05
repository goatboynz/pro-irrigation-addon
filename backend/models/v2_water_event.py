"""
Water Event model for v2 room-based irrigation system.

Water events represent scheduled irrigation events (P1 or P2) for a room.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from .v2_zone import event_zones_v2


class WaterEvent(Base):
    """
    Water Event model representing a scheduled irrigation event.
    
    Event Types:
        - P1: Primary event, occurs once per day at lights-on + delay
        - P2: Secondary event, occurs at specific time of day
    
    Attributes:
        id: Primary key
        room_id: Foreign key to rooms table
        event_type: 'p1' or 'p2'
        name: User-friendly event name
        delay_minutes: Minutes after lights-on (P1 only)
        time_of_day: HH:MM format (P2 only)
        run_time_seconds: Duration in total seconds
        enabled: Whether the event is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        
    Relationships:
        room: Parent room
        zones: List of zones that execute this event
    """
    __tablename__ = "water_events"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(10), nullable=False)  # 'p1' or 'p2'
    name = Column(String(100), nullable=False)
    
    # P1 specific
    delay_minutes = Column(Integer, nullable=True)
    
    # P2 specific
    time_of_day = Column(String(5), nullable=True)  # HH:MM format
    
    # Common
    run_time_seconds = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    room = relationship("Room", back_populates="water_events")
    zones = relationship("ZoneV2", secondary=event_zones_v2, back_populates="water_events")
    
    def __repr__(self):
        return f"<WaterEvent(id={self.id}, type='{self.event_type}', name='{self.name}', room_id={self.room_id})>"
