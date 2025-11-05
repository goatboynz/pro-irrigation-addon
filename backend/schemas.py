"""
Pydantic schemas for v2 room-based irrigation system.

This module provides request and response schemas for all models:
- Room
- Pump
- Zone
- WaterEvent
- EnvironmentalSensor
- SystemSettings
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


# ============================================================================
# Room Schemas
# ============================================================================

class RoomBase(BaseModel):
    """Base schema for Room with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique room name")
    lights_on_entity: Optional[str] = Field(None, max_length=255, description="HA input_datetime entity for lights-on time")
    lights_off_entity: Optional[str] = Field(None, max_length=255, description="HA input_datetime entity for lights-off time")
    enabled: bool = Field(True, description="Whether the room is active")


class RoomCreate(RoomBase):
    """Schema for creating a new room."""
    pass


class RoomUpdate(BaseModel):
    """Schema for updating an existing room."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    lights_on_entity: Optional[str] = Field(None, max_length=255)
    lights_off_entity: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class RoomResponse(RoomBase):
    """Schema for room response with relationships."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoomDetailResponse(RoomResponse):
    """Schema for detailed room response with all relationships."""
    pumps: List['PumpResponse'] = []
    water_events: List['WaterEventResponse'] = []
    sensors: List['SensorResponse'] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Pump Schemas
# ============================================================================

class PumpBase(BaseModel):
    """Base schema for Pump with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Pump name")
    lock_entity: str = Field(..., max_length=255, description="HA input_boolean entity for pump lock")
    enabled: bool = Field(True, description="Whether the pump is active")


class PumpCreate(PumpBase):
    """Schema for creating a new pump."""
    pass


class PumpUpdate(BaseModel):
    """Schema for updating an existing pump."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    lock_entity: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class PumpResponse(PumpBase):
    """Schema for pump response with relationships."""
    id: int
    room_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PumpDetailResponse(PumpResponse):
    """Schema for detailed pump response with zones."""
    zones: List['ZoneResponse'] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Zone Schemas
# ============================================================================

class ZoneBase(BaseModel):
    """Base schema for Zone with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Zone name")
    switch_entity: str = Field(..., max_length=255, description="HA switch entity to control zone")
    enabled: bool = Field(True, description="Whether the zone is active")


class ZoneCreate(ZoneBase):
    """Schema for creating a new zone."""
    pass


class ZoneUpdate(BaseModel):
    """Schema for updating an existing zone."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    switch_entity: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class ZoneResponse(ZoneBase):
    """Schema for zone response."""
    id: int
    pump_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Water Event Schemas
# ============================================================================

class WaterEventBase(BaseModel):
    """Base schema for WaterEvent with common fields."""
    event_type: str = Field(..., pattern="^(p1|p2)$", description="Event type: 'p1' or 'p2'")
    name: str = Field(..., min_length=1, max_length=100, description="User-friendly event name")
    delay_minutes: Optional[int] = Field(None, ge=0, description="Minutes after lights-on (P1 only)")
    time_of_day: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="HH:MM format (P2 only)")
    run_time_seconds: int = Field(..., gt=0, description="Duration in total seconds")
    enabled: bool = Field(True, description="Whether the event is active")
    
    @field_validator('delay_minutes', 'time_of_day')
    @classmethod
    def validate_event_type_fields(cls, v, info):
        """Validate that P1 events have delay_minutes and P2 events have time_of_day."""
        event_type = info.data.get('event_type')
        field_name = info.field_name
        
        if event_type == 'p1' and field_name == 'delay_minutes' and v is None:
            raise ValueError('delay_minutes is required for P1 events')
        if event_type == 'p1' and field_name == 'time_of_day' and v is not None:
            raise ValueError('time_of_day should not be set for P1 events')
        if event_type == 'p2' and field_name == 'time_of_day' and v is None:
            raise ValueError('time_of_day is required for P2 events')
        if event_type == 'p2' and field_name == 'delay_minutes' and v is not None:
            raise ValueError('delay_minutes should not be set for P2 events')
        
        return v


class WaterEventCreate(WaterEventBase):
    """Schema for creating a new water event."""
    zone_ids: List[int] = Field(default_factory=list, description="List of zone IDs to assign to this event")


class WaterEventUpdate(BaseModel):
    """Schema for updating an existing water event."""
    event_type: Optional[str] = Field(None, pattern="^(p1|p2)$")
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    delay_minutes: Optional[int] = Field(None, ge=0)
    time_of_day: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    run_time_seconds: Optional[int] = Field(None, gt=0)
    enabled: Optional[bool] = None


class WaterEventResponse(WaterEventBase):
    """Schema for water event response."""
    id: int
    room_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WaterEventDetailResponse(WaterEventResponse):
    """Schema for detailed water event response with zones."""
    zones: List[ZoneResponse] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Environmental Sensor Schemas
# ============================================================================

class SensorBase(BaseModel):
    """Base schema for EnvironmentalSensor with common fields."""
    sensor_entity: str = Field(..., max_length=255, description="HA sensor entity ID")
    display_name: str = Field(..., min_length=1, max_length=100, description="User-friendly name")
    sensor_type: str = Field(..., max_length=50, description="Type: soil_rh, ec, temperature, humidity, other")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    enabled: bool = Field(True, description="Whether the sensor is active")


class SensorCreate(SensorBase):
    """Schema for creating a new sensor."""
    pass


class SensorUpdate(BaseModel):
    """Schema for updating an existing sensor."""
    sensor_entity: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    sensor_type: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    enabled: Optional[bool] = None


class SensorResponse(SensorBase):
    """Schema for sensor response."""
    id: int
    room_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# System Settings Schemas
# ============================================================================

class SystemSettingsBase(BaseModel):
    """Base schema for SystemSettings with common fields."""
    pump_startup_delay_seconds: int = Field(..., ge=0, description="Delay before opening zone after pump starts")
    zone_switch_delay_seconds: int = Field(..., ge=0, description="Delay between closing one zone and opening next")
    scheduler_interval_seconds: int = Field(..., ge=1, description="How often scheduler checks for events")


class SystemSettingsUpdate(SystemSettingsBase):
    """Schema for updating system settings."""
    pass


class SystemSettingsResponse(SystemSettingsBase):
    """Schema for system settings response."""
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Update forward references for nested models
RoomDetailResponse.model_rebuild()
PumpDetailResponse.model_rebuild()
WaterEventDetailResponse.model_rebuild()
