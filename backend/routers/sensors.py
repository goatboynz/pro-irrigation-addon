"""
Sensors API router for v2 room-based irrigation system.

This module provides CRUD endpoints for managing environmental sensors:
- GET /api/rooms/{room_id}/sensors - List sensors for room
- POST /api/rooms/{room_id}/sensors - Create sensor
- PUT /api/sensors/{id} - Update sensor
- DELETE /api/sensors/{id} - Delete sensor
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import aiohttp

from backend.models.database import get_db
from backend.models.v2_room import Room
from backend.models.v2_sensor import EnvironmentalSensor
from backend.schemas import (
    SensorCreate,
    SensorUpdate,
    SensorResponse
)
from backend.services.ha_client import validate_sensor_entity, get_ha_client

router = APIRouter(prefix="/api", tags=["Sensors"])


# ============================================================================
# Sensor Data Schemas
# ============================================================================

class SensorCurrentValue(BaseModel):
    """Schema for current sensor value response."""
    sensor_id: int
    sensor_entity: str
    display_name: str
    current_value: Optional[str]
    unit: Optional[str]
    last_updated: Optional[str]


class SensorHistoryPoint(BaseModel):
    """Schema for a single historical data point."""
    timestamp: str
    value: Optional[str]


class SensorHistory(BaseModel):
    """Schema for sensor historical data response."""
    sensor_id: int
    sensor_entity: str
    display_name: str
    unit: Optional[str]
    duration: str
    data_points: List[SensorHistoryPoint]


@router.get("/rooms/{room_id}/sensors", response_model=List[SensorResponse])
def list_sensors(room_id: int, db: Session = Depends(get_db)):
    """
    List all sensors for a specific room.
    
    Args:
        room_id: Room ID
        db: Database session
        
    Returns:
        List[SensorResponse]: List of sensors in the room
        
    Raises:
        HTTPException: 404 if room not found
    """
    # Verify room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    sensors = db.query(EnvironmentalSensor).filter(
        EnvironmentalSensor.room_id == room_id
    ).all()
    
    return sensors


@router.post("/rooms/{room_id}/sensors", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor(room_id: int, sensor_data: SensorCreate, db: Session = Depends(get_db)):
    """
    Create a new sensor for a room.
    
    Args:
        room_id: Room ID
        sensor_data: Sensor creation data
        db: Database session
        
    Returns:
        SensorResponse: Created sensor
        
    Raises:
        HTTPException: 404 if room not found
        HTTPException: 400 if sensor entity is invalid
    """
    # Verify room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    # Validate sensor entity exists in Home Assistant
    is_valid = await validate_sensor_entity(sensor_data.sensor_entity)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor entity '{sensor_data.sensor_entity}' not found in Home Assistant or is not a sensor"
        )
    
    # Create new sensor
    new_sensor = EnvironmentalSensor(
        room_id=room_id,
        sensor_entity=sensor_data.sensor_entity,
        display_name=sensor_data.display_name,
        sensor_type=sensor_data.sensor_type,
        unit=sensor_data.unit,
        enabled=sensor_data.enabled
    )
    
    db.add(new_sensor)
    db.commit()
    db.refresh(new_sensor)
    
    return new_sensor


@router.put("/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor(sensor_id: int, sensor_data: SensorUpdate, db: Session = Depends(get_db)):
    """
    Update an existing sensor.
    
    Args:
        sensor_id: Sensor ID
        sensor_data: Sensor update data
        db: Database session
        
    Returns:
        SensorResponse: Updated sensor
        
    Raises:
        HTTPException: 404 if sensor not found
        HTTPException: 400 if new sensor entity is invalid
    """
    sensor = db.query(EnvironmentalSensor).filter(EnvironmentalSensor.id == sensor_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )
    
    # If sensor_entity is being updated, validate it
    if sensor_data.sensor_entity is not None and sensor_data.sensor_entity != sensor.sensor_entity:
        is_valid = await validate_sensor_entity(sensor_data.sensor_entity)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sensor entity '{sensor_data.sensor_entity}' not found in Home Assistant or is not a sensor"
            )
    
    # Update fields if provided
    update_data = sensor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sensor, field, value)
    
    db.commit()
    db.refresh(sensor)
    
    return sensor


@router.delete("/sensors/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """
    Delete a sensor.
    
    Args:
        sensor_id: Sensor ID
        db: Database session
        
    Raises:
        HTTPException: 404 if sensor not found
    """
    sensor = db.query(EnvironmentalSensor).filter(EnvironmentalSensor.id == sensor_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )
    
    db.delete(sensor)
    db.commit()
    
    return None



# ============================================================================
# Sensor Data Endpoints
# ============================================================================

@router.get("/sensors/{sensor_id}/current", response_model=SensorCurrentValue)
async def get_sensor_current_value(sensor_id: int, db: Session = Depends(get_db)):
    """
    Get the current value of a sensor from Home Assistant.
    
    This endpoint queries Home Assistant in real-time to get the
    current state and value of the sensor entity.
    
    Args:
        sensor_id: Sensor ID
        db: Database session
        
    Returns:
        SensorCurrentValue: Current sensor value and metadata
        
    Raises:
        HTTPException: 404 if sensor not found
        HTTPException: 500 if unable to get value from Home Assistant
    """
    # Get sensor from database
    sensor = db.query(EnvironmentalSensor).filter(EnvironmentalSensor.id == sensor_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )
    
    # Get current state from Home Assistant
    ha_client = get_ha_client()
    
    try:
        entity_state = await ha_client.get_state(sensor.sensor_entity)
        
        return SensorCurrentValue(
            sensor_id=sensor.id,
            sensor_entity=sensor.sensor_entity,
            display_name=sensor.display_name,
            current_value=entity_state.state,
            unit=sensor.unit or entity_state.attributes.get("unit_of_measurement"),
            last_updated=entity_state.attributes.get("last_updated")
        )
    except ValueError as e:
        # Entity not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor entity '{sensor.sensor_entity}' not found in Home Assistant"
        )
    except Exception as e:
        # Other errors (API failure, etc.)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sensor value from Home Assistant: {str(e)}"
        )


@router.get("/sensors/{sensor_id}/history", response_model=SensorHistory)
async def get_sensor_history(
    sensor_id: int,
    duration: str = Query("1h", description="Duration to fetch history for (e.g., '1h', '24h', '7d')"),
    db: Session = Depends(get_db)
):
    """
    Get historical data for a sensor from Home Assistant.
    
    This endpoint queries Home Assistant's history API to retrieve
    historical sensor values over a specified duration.
    
    Duration format:
    - '1h' = 1 hour
    - '24h' = 24 hours
    - '7d' = 7 days
    
    Args:
        sensor_id: Sensor ID
        duration: Time duration to fetch (default: '1h')
        db: Database session
        
    Returns:
        SensorHistory: Historical sensor data points
        
    Raises:
        HTTPException: 404 if sensor not found
        HTTPException: 400 if duration format is invalid
        HTTPException: 500 if unable to get history from Home Assistant
    """
    # Get sensor from database
    sensor = db.query(EnvironmentalSensor).filter(EnvironmentalSensor.id == sensor_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )
    
    # Parse duration string
    try:
        duration_seconds = _parse_duration(duration)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Calculate start time
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(seconds=duration_seconds)
    
    # Get Home Assistant client
    ha_client = get_ha_client()
    
    # Query history from Home Assistant
    try:
        history_data = await _get_ha_history(
            ha_client,
            sensor.sensor_entity,
            start_time,
            end_time
        )
        
        # Convert to response format
        data_points = []
        for point in history_data:
            data_points.append(SensorHistoryPoint(
                timestamp=point.get("last_updated", point.get("last_changed", "")),
                value=point.get("state")
            ))
        
        return SensorHistory(
            sensor_id=sensor.id,
            sensor_entity=sensor.sensor_entity,
            display_name=sensor.display_name,
            unit=sensor.unit,
            duration=duration,
            data_points=data_points
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sensor history from Home Assistant: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_duration(duration: str) -> int:
    """
    Parse a duration string into seconds.
    
    Supported formats:
    - '1h', '2h', etc. (hours)
    - '30m', '45m', etc. (minutes)
    - '1d', '7d', etc. (days)
    
    Args:
        duration: Duration string
        
    Returns:
        int: Duration in seconds
        
    Raises:
        ValueError: If duration format is invalid
    """
    duration = duration.strip().lower()
    
    if not duration:
        raise ValueError("Duration cannot be empty")
    
    # Extract number and unit
    if duration[-1] == 'h':
        # Hours
        try:
            hours = int(duration[:-1])
            return hours * 3600
        except ValueError:
            raise ValueError(f"Invalid duration format: '{duration}'. Expected format like '1h', '24h'")
    elif duration[-1] == 'm':
        # Minutes
        try:
            minutes = int(duration[:-1])
            return minutes * 60
        except ValueError:
            raise ValueError(f"Invalid duration format: '{duration}'. Expected format like '30m', '45m'")
    elif duration[-1] == 'd':
        # Days
        try:
            days = int(duration[:-1])
            return days * 86400
        except ValueError:
            raise ValueError(f"Invalid duration format: '{duration}'. Expected format like '1d', '7d'")
    else:
        raise ValueError(f"Invalid duration format: '{duration}'. Use 'h' for hours, 'm' for minutes, or 'd' for days")


async def _get_ha_history(
    ha_client,
    entity_id: str,
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Get historical data from Home Assistant history API.
    
    Args:
        ha_client: HomeAssistantClient instance
        entity_id: Entity ID to query
        start_time: Start time for history
        end_time: End time for history
        
    Returns:
        List of historical state data points
        
    Raises:
        aiohttp.ClientError: If the API request fails
    """
    # Format timestamps for HA API (ISO 8601)
    start_timestamp = start_time.isoformat() + "Z"
    end_timestamp = end_time.isoformat() + "Z"
    
    # Build history API URL
    url = f"{ha_client.base_url}/history/period/{start_timestamp}"
    params = {
        "filter_entity_id": entity_id,
        "end_time": end_timestamp
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=ha_client.headers, params=params) as response:
                response.raise_for_status()
                history = await response.json()
                
                # History API returns a list of lists (one per entity)
                # We only queried one entity, so get the first list
                if history and len(history) > 0:
                    return history[0]
                else:
                    return []
                    
    except aiohttp.ClientError as e:
        raise Exception(f"Failed to query Home Assistant history API: {e}")
