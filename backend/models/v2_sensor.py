"""
Environmental Sensor model for v2 room-based irrigation system.

Sensors track environmental conditions in a room.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class EnvironmentalSensor(Base):
    """
    Environmental Sensor model for monitoring room conditions.
    
    Sensor Types:
        - soil_rh: Soil relative humidity/moisture
        - ec: Electrical conductivity
        - temperature: Temperature
        - humidity: Air humidity
        - other: Custom sensor type
    
    Attributes:
        id: Primary key
        room_id: Foreign key to rooms table
        sensor_entity: HA sensor entity ID
        display_name: User-friendly name
        sensor_type: Type of sensor
        unit: Unit of measurement (optional)
        enabled: Whether the sensor is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        
    Relationships:
        room: Parent room
    """
    __tablename__ = "environmental_sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_entity = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # soil_rh, ec, temperature, humidity, other
    unit = Column(String(20), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    room = relationship("Room", back_populates="sensors")
    
    def __repr__(self):
        return f"<EnvironmentalSensor(id={self.id}, name='{self.display_name}', type='{self.sensor_type}')>"
