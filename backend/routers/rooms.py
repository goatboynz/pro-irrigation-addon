"""
Rooms API router for v2 room-based irrigation system.

This module provides CRUD endpoints for managing rooms:
- GET /api/rooms - List all rooms
- POST /api/rooms - Create room
- GET /api/rooms/{id} - Get room with relationships
- PUT /api/rooms/{id} - Update room
- DELETE /api/rooms/{id} - Delete room (cascade)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.models.database import get_db
from backend.models.v2_room import Room
from backend.models.v2_pump import PumpV2
from backend.models.v2_water_event import WaterEvent
from backend.schemas import (
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    RoomDetailResponse
)
from backend.services.ha_client import get_ha_client

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


@router.get("", response_model=List[RoomResponse])
def list_rooms(db: Session = Depends(get_db)):
    """
    List all rooms.
    
    Returns:
        List[RoomResponse]: List of all rooms with basic information
    """
    rooms = db.query(Room).all()
    return rooms


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    """
    Create a new room.
    
    Args:
        room_data: Room creation data
        db: Database session
        
    Returns:
        RoomResponse: Created room
        
    Raises:
        HTTPException: 400 if room name already exists
    """
    # Check if room with same name already exists
    existing_room = db.query(Room).filter(Room.name == room_data.name).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with name '{room_data.name}' already exists"
        )
    
    # Create new room
    new_room = Room(
        name=room_data.name,
        lights_on_entity=room_data.lights_on_entity,
        lights_off_entity=room_data.lights_off_entity,
        enabled=room_data.enabled
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    return new_room


@router.get("/{room_id}", response_model=RoomDetailResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """
    Get a specific room with all relationships (pumps, water events, sensors).
    
    Args:
        room_id: Room ID
        db: Database session
        
    Returns:
        RoomDetailResponse: Room with all related entities
        
    Raises:
        HTTPException: 404 if room not found
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    return room


@router.put("/{room_id}", response_model=RoomResponse)
def update_room(room_id: int, room_data: RoomUpdate, db: Session = Depends(get_db)):
    """
    Update an existing room.
    
    Args:
        room_id: Room ID
        room_data: Room update data
        db: Database session
        
    Returns:
        RoomResponse: Updated room
        
    Raises:
        HTTPException: 404 if room not found
        HTTPException: 400 if new name conflicts with existing room
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    # Check if new name conflicts with existing room
    if room_data.name is not None and room_data.name != room.name:
        existing_room = db.query(Room).filter(Room.name == room_data.name).first()
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room with name '{room_data.name}' already exists"
            )
    
    # Update fields if provided
    update_data = room_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    """
    Delete a room and all related entities (cascade).
    
    This will delete:
    - The room itself
    - All pumps in the room
    - All zones associated with those pumps
    - All water events for the room
    - All sensors in the room
    
    Args:
        room_id: Room ID
        db: Database session
        
    Raises:
        HTTPException: 404 if room not found
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    db.delete(room)
    db.commit()
    
    return None


# ============================================================================
# Room Status Endpoint
# ============================================================================

class PumpStatus(BaseModel):
    """Schema for pump status information."""
    pump_id: int
    pump_name: str
    lock_entity: str
    is_locked: bool
    enabled: bool


class ActiveEvent(BaseModel):
    """Schema for active water event information."""
    event_id: int
    event_name: str
    event_type: str
    zones_count: int


class RoomStatus(BaseModel):
    """Schema for room status response."""
    room_id: int
    room_name: str
    enabled: bool
    pumps: List[PumpStatus]
    active_events: List[ActiveEvent]


@router.get("/{room_id}/status", response_model=RoomStatus)
async def get_room_status(room_id: int, db: Session = Depends(get_db)):
    """
    Get current status of a room including pump states and active events.
    
    This endpoint provides real-time status information:
    - Pump lock states (queried from Home Assistant)
    - Active water events (enabled events with assigned zones)
    
    Args:
        room_id: Room ID
        db: Database session
        
    Returns:
        RoomStatus: Current room status with pump and event information
        
    Raises:
        HTTPException: 404 if room not found
    """
    # Get room
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    # Get Home Assistant client
    ha_client = get_ha_client()
    
    # Get pump statuses
    pump_statuses = []
    pumps = db.query(PumpV2).filter(PumpV2.room_id == room_id).all()
    
    for pump in pumps:
        # Query lock state from Home Assistant
        is_locked = False
        try:
            is_locked = await ha_client.is_entity_on(pump.lock_entity)
        except Exception as e:
            # If we can't get the state, default to False and log the error
            print(f"Warning: Could not get lock state for {pump.lock_entity}: {e}")
        
        pump_statuses.append(PumpStatus(
            pump_id=pump.id,
            pump_name=pump.name,
            lock_entity=pump.lock_entity,
            is_locked=is_locked,
            enabled=pump.enabled
        ))
    
    # Get active events (enabled events with at least one zone assigned)
    active_events = []
    water_events = db.query(WaterEvent).filter(
        WaterEvent.room_id == room_id,
        WaterEvent.enabled == True
    ).all()
    
    for event in water_events:
        # Count assigned zones
        zones_count = len(event.zones)
        
        # Only include events that have zones assigned
        if zones_count > 0:
            active_events.append(ActiveEvent(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                zones_count=zones_count
            ))
    
    return RoomStatus(
        room_id=room.id,
        room_name=room.name,
        enabled=room.enabled,
        pumps=pump_statuses,
        active_events=active_events
    )
