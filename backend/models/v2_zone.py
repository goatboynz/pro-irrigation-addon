"""
Zone model for v2 room-based irrigation system.

A Zone represents an irrigation zone controlled by a switch entity.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# Association table for many-to-many relationship between events and zones
event_zones_v2 = Table(
    'event_zones_v2',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('water_events.id', ondelete='CASCADE'), primary_key=True),
    Column('zone_id', Integer, ForeignKey('zones_v2.id', ondelete='CASCADE'), primary_key=True)
)


class ZoneV2(Base):
    """
    Zone model representing an irrigation zone.
    
    Attributes:
        id: Primary key
        pump_id: Foreign key to pumps table
        name: Zone name (unique within pump)
        switch_entity: HA switch entity to control zone
        enabled: Whether the zone is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        
    Relationships:
        pump: Parent pump
        water_events: List of water events that include this zone
    """
    __tablename__ = "zones_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    pump_id = Column(Integer, ForeignKey("pumps_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    switch_entity = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    pump = relationship("PumpV2", back_populates="zones")
    water_events = relationship("WaterEvent", secondary=event_zones_v2, back_populates="zones")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('pump_id', 'name', name='uq_zone_name_per_pump'),
    )
    
    def __repr__(self):
        return f"<ZoneV2(id={self.id}, name='{self.name}', pump_id={self.pump_id})>"
