"""
Pump model for v2 room-based irrigation system.

A Pump represents physical pump hardware within a room.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class PumpV2(Base):
    """
    Pump model representing physical pump hardware.
    
    Attributes:
        id: Primary key
        room_id: Foreign key to rooms table
        name: Pump name (unique within room)
        lock_entity: HA input_boolean entity for pump lock
        enabled: Whether the pump is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        
    Relationships:
        room: Parent room
        zones: List of zones connected to this pump
    """
    __tablename__ = "pumps_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    lock_entity = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    room = relationship("Room", back_populates="pumps")
    zones = relationship("ZoneV2", back_populates="pump", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('room_id', 'name', name='uq_pump_name_per_room'),
    )
    
    def __repr__(self):
        return f"<PumpV2(id={self.id}, name='{self.name}', room_id={self.room_id})>"
