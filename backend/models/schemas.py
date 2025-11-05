"""
Pydantic schemas for API request/response validation.

This module defines all the data transfer objects (DTOs) used by the FastAPI
endpoints for request validation and response serialization.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


# ============================================================================
# Pump Schemas
# ============================================================================

class PumpCreate(BaseModel):
    """Schema for creating a new pump."""
    name: str = Field(..., min_length=1, max_length=100, description="Pump name")
    lock_entity: str = Field(..., min_length=1, max_length=255, description="Home Assistant lock entity ID")


class PumpUpdate(BaseModel):
    """Schema for updating an existing pump."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Pump name")
    lock_entity: Optional[str] = Field(None, min_length=1, max_length=255, description="Home Assistant lock entity ID")


class PumpResponse(BaseModel):
    """Schema for pump response with status information."""
    id: int
    name: str
    lock_entity: str
    status: str = Field(..., description="Pump status: idle, running, or queued")
    active_zone: Optional[str] = Field(None, description="Name of currently active zone if running")
    queue_length: int = Field(..., description="Number of jobs in pump queue")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PumpBasic(BaseModel):
    """Basic pump information without status."""
    id: int
    name: str
    lock_entity: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Zone Schemas
# ============================================================================

class ZoneCreate(BaseModel):
    """Schema for creating a new zone."""
    name: str = Field(..., min_length=1, max_length=100, description="Zone name")
    switch_entity: str = Field(..., min_length=1, max_length=255, description="Home Assistant switch entity ID")
    mode: Literal['auto', 'manual'] = Field(..., description="Scheduling mode: auto or manual")
    
    # Auto mode fields
    p1_duration_sec: Optional[int] = Field(None, ge=0, description="P1 event duration in seconds (auto mode)")
    p2_event_count: Optional[int] = Field(None, ge=0, description="Number of P2 events (auto mode)")
    p2_duration_sec: Optional[int] = Field(None, ge=0, description="P2 event duration in seconds (auto mode)")
    
    # Manual mode fields
    p1_manual_list: Optional[str] = Field(None, description="P1 event list in HH:MM.SS format (manual mode)")
    p2_manual_list: Optional[str] = Field(None, description="P2 event list in HH:MM.SS format (manual mode)")
    
    # Zone status
    enabled: bool = Field(True, description="Whether the zone is enabled")
    
    @validator('p1_duration_sec', 'p2_event_count', 'p2_duration_sec')
    def validate_auto_fields(cls, v, values, field):
        """Validate that auto mode fields are provided when mode is auto."""
        if 'mode' in values and values['mode'] == 'auto':
            if field.name in ['p1_duration_sec', 'p2_duration_sec'] and v is None:
                raise ValueError(f"{field.name} is required for auto mode")
        return v
    
    @validator('p1_manual_list', 'p2_manual_list')
    def validate_manual_fields(cls, v, values, field):
        """Validate manual schedule format."""
        if v is not None and v.strip():
            # Import here to avoid circular dependency
            from ..services.calculator import validate_manual_schedule_format
            is_valid, error_msg = validate_manual_schedule_format(v)
            if not is_valid:
                raise ValueError(f"Invalid manual schedule format: {error_msg}")
        return v


class ZoneUpdate(BaseModel):
    """Schema for updating an existing zone."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Zone name")
    switch_entity: Optional[str] = Field(None, min_length=1, max_length=255, description="Home Assistant switch entity ID")
    mode: Optional[Literal['auto', 'manual']] = Field(None, description="Scheduling mode: auto or manual")
    
    # Auto mode fields
    p1_duration_sec: Optional[int] = Field(None, ge=0, description="P1 event duration in seconds (auto mode)")
    p2_event_count: Optional[int] = Field(None, ge=0, description="Number of P2 events (auto mode)")
    p2_duration_sec: Optional[int] = Field(None, ge=0, description="P2 event duration in seconds (auto mode)")
    
    # Manual mode fields
    p1_manual_list: Optional[str] = Field(None, description="P1 event list in HH:MM.SS format (manual mode)")
    p2_manual_list: Optional[str] = Field(None, description="P2 event list in HH:MM.SS format (manual mode)")
    
    # Zone status
    enabled: Optional[bool] = Field(None, description="Whether the zone is enabled")
    
    @validator('p1_manual_list', 'p2_manual_list')
    def validate_manual_fields(cls, v):
        """Validate manual schedule format."""
        if v is not None and v.strip():
            from ..services.calculator import validate_manual_schedule_format
            is_valid, error_msg = validate_manual_schedule_format(v)
            if not is_valid:
                raise ValueError(f"Invalid manual schedule format: {error_msg}")
        return v


class ZoneResponse(BaseModel):
    """Schema for zone response with next run information."""
    id: int
    pump_id: int
    name: str
    switch_entity: str
    mode: str
    p1_duration_sec: Optional[int]
    p2_event_count: Optional[int]
    p2_duration_sec: Optional[int]
    p1_manual_list: Optional[str]
    p2_manual_list: Optional[str]
    enabled: bool
    next_run: Optional[datetime] = Field(None, description="Next scheduled run time")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ZoneBasic(BaseModel):
    """Basic zone information without next run calculation."""
    id: int
    pump_id: int
    name: str
    switch_entity: str
    mode: str
    p1_duration_sec: Optional[int]
    p2_event_count: Optional[int]
    p2_duration_sec: Optional[int]
    p1_manual_list: Optional[str]
    p2_manual_list: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Global Settings Schemas
# ============================================================================

class GlobalSettingsUpdate(BaseModel):
    """Schema for updating global settings."""
    lights_on_entity: Optional[str] = Field(None, max_length=255, description="Lights on time entity")
    lights_off_entity: Optional[str] = Field(None, max_length=255, description="Lights off time entity")
    p1_delay_entity: Optional[str] = Field(None, max_length=255, description="P1 start delay entity")
    p2_delay_entity: Optional[str] = Field(None, max_length=255, description="P2 start delay entity")
    p2_buffer_entity: Optional[str] = Field(None, max_length=255, description="P2 end buffer entity")
    feed_notes: Optional[str] = Field(None, description="Feed schedule notes")


class GlobalSettingsResponse(BaseModel):
    """Schema for global settings response."""
    id: int
    lights_on_entity: Optional[str]
    lights_off_entity: Optional[str]
    p1_delay_entity: Optional[str]
    p2_delay_entity: Optional[str]
    p2_buffer_entity: Optional[str]
    feed_notes: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Entity Discovery Schemas
# ============================================================================

class EntityResponse(BaseModel):
    """Schema for Home Assistant entity information."""
    entity_id: str = Field(..., description="Entity ID")
    friendly_name: str = Field(..., description="Human-readable entity name")
    state: str = Field(..., description="Current entity state")


# ============================================================================
# System Status Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Health status: healthy or unhealthy")
    database: str = Field(..., description="Database status: connected or disconnected")
    timestamp: datetime = Field(..., description="Health check timestamp")


class SystemStatusResponse(BaseModel):
    """Schema for system status response."""
    status: str = Field(..., description="Overall system status")
    database_healthy: bool
    total_pumps: int
    total_zones: int
    enabled_zones: int
    timestamp: datetime


# ============================================================================
# Next Run Schemas
# ============================================================================

class NextRunResponse(BaseModel):
    """Schema for zone next run time response."""
    zone_id: int
    zone_name: str
    next_run: Optional[datetime] = Field(None, description="Next scheduled run time, or null if no upcoming events")
