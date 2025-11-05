"""Pump model for irrigation system."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class Pump(Base):
    """
    Pump model representing a physical water pump.
    
    A pump can have multiple zones and uses a lock entity to prevent
    simultaneous zone execution.
    """
    
    __tablename__ = "pumps"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lock_entity = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to zones - cascade delete orphaned zones when pump is deleted
    zones = relationship(
        "Zone",
        back_populates="pump",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Pump(id={self.id}, name='{self.name}', lock_entity='{self.lock_entity}')>"
