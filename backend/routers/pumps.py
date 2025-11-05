"""
Pumps API router for v2 room-based irrigation system.

This module provides CRUD endpoints for managing pumps:
- GET /api/rooms/{room_id}/pumps - List pumps for room
- POST /api/rooms/{room_id}/pumps - Create pump
- PUT /api/pumps/{id} - Update pump
- DELETE /api/pumps/{id} - Delete pump (cascade)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.models.database import get_db
from backend.models.v2_room import Room
from backend.models.v2_pump import PumpV2
from backend.models.v2_zone import ZoneV2
from backend.schemas import (
    PumpCreate,
    PumpUpdate,
    PumpResponse,
    PumpDetailResponse
)
from backend.services.ha_client import get_ha_client

router = APIRouter(prefix="/api", tags=["Pumps"])


@router.get("/rooms/{room_id}/pumps", response_model=List[PumpResponse])
def list_pumps_for_room(room_id: int, db: Session = Depends(get_db)):
    """
    List all pumps for a specific room.
    
    Args:
        room_id: Room ID
        db: Database session
        
    Returns:
        List[PumpResponse]: List of pumps in the room
        
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
    
    # Get all pumps for the room
    pumps = db.query(PumpV2).filter(PumpV2.room_id == room_id).all()
    return pumps


@router.post("/rooms/{room_id}/pumps", response_model=PumpResponse, status_code=status.HTTP_201_CREATED)
def create_pump(room_id: int, pump_data: PumpCreate, db: Session = Depends(get_db)):
    """
    Create a new pump in a room.
    
    Args:
        room_id: Room ID
        pump_data: Pump creation data
        db: Database session
        
    Returns:
        PumpResponse: Created pump
        
    Raises:
        HTTPException: 404 if room not found
        HTTPException: 400 if pump name already exists in room
    """
    # Verify room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    # Check if pump with same name already exists in this room
    existing_pump = db.query(PumpV2).filter(
        PumpV2.room_id == room_id,
        PumpV2.name == pump_data.name
    ).first()
    if existing_pump:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pump with name '{pump_data.name}' already exists in this room"
        )
    
    # Create new pump
    new_pump = PumpV2(
        room_id=room_id,
        name=pump_data.name,
        lock_entity=pump_data.lock_entity,
        enabled=pump_data.enabled
    )
    
    db.add(new_pump)
    db.commit()
    db.refresh(new_pump)
    
    return new_pump


@router.put("/pumps/{pump_id}", response_model=PumpResponse)
def update_pump(pump_id: int, pump_data: PumpUpdate, db: Session = Depends(get_db)):
    """
    Update an existing pump.
    
    Args:
        pump_id: Pump ID
        pump_data: Pump update data
        db: Database session
        
    Returns:
        PumpResponse: Updated pump
        
    Raises:
        HTTPException: 404 if pump not found
        HTTPException: 400 if new name conflicts with existing pump in same room
    """
    pump = db.query(PumpV2).filter(PumpV2.id == pump_id).first()
    
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {pump_id} not found"
        )
    
    # Check if new name conflicts with existing pump in same room
    if pump_data.name is not None and pump_data.name != pump.name:
        existing_pump = db.query(PumpV2).filter(
            PumpV2.room_id == pump.room_id,
            PumpV2.name == pump_data.name
        ).first()
        if existing_pump:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pump with name '{pump_data.name}' already exists in this room"
            )
    
    # Update fields if provided
    update_data = pump_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pump, field, value)
    
    db.commit()
    db.refresh(pump)
    
    return pump


@router.delete("/pumps/{pump_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pump(pump_id: int, db: Session = Depends(get_db)):
    """
    Delete a pump and all related zones (cascade).
    
    This will delete:
    - The pump itself
    - All zones associated with this pump
    
    Args:
        pump_id: Pump ID
        db: Database session
        
    Raises:
        HTTPException: 404 if pump not found
    """
    pump = db.query(PumpV2).filter(PumpV2.id == pump_id).first()
    
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {pump_id} not found"
        )
    
    db.delete(pump)
    db.commit()
    
    return None


# ============================================================================
# Pump Status Endpoint
# ============================================================================

class ActiveZoneInfo(BaseModel):
    """Schema for active zone information."""
    zone_id: int
    zone_name: str
    switch_entity: str


class PumpStatusResponse(BaseModel):
    """Schema for pump status response."""
    pump_id: int
    pump_name: str
    lock_entity: str
    is_locked: bool
    enabled: bool
    active_zone: Optional[ActiveZoneInfo]
    queue_length: int


@router.get("/pumps/{pump_id}/status", response_model=PumpStatusResponse)
async def get_pump_status(pump_id: int, db: Session = Depends(get_db)):
    """
    Get current status of a pump including lock state, active zone, and queue length.
    
    This endpoint provides real-time status information:
    - Lock state (queried from Home Assistant)
    - Active zone (if pump is currently running)
    - Queue length (number of pending jobs)
    
    Args:
        pump_id: Pump ID
        db: Database session
        
    Returns:
        PumpStatusResponse: Current pump status
        
    Raises:
        HTTPException: 404 if pump not found
    """
    # Get pump
    pump = db.query(PumpV2).filter(PumpV2.id == pump_id).first()
    
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {pump_id} not found"
        )
    
    # Get Home Assistant client
    ha_client = get_ha_client()
    
    # Query lock state from Home Assistant
    is_locked = False
    try:
        is_locked = await ha_client.is_entity_on(pump.lock_entity)
    except Exception as e:
        # If we can't get the state, default to False and log the error
        print(f"Warning: Could not get lock state for {pump.lock_entity}: {e}")
    
    # Determine active zone by checking which zone switch is on
    active_zone = None
    if is_locked:
        # Get all zones for this pump
        zones = db.query(ZoneV2).filter(ZoneV2.pump_id == pump_id).all()
        
        # Check each zone's switch state
        for zone in zones:
            try:
                if await ha_client.is_entity_on(zone.switch_entity):
                    active_zone = ActiveZoneInfo(
                        zone_id=zone.id,
                        zone_name=zone.name,
                        switch_entity=zone.switch_entity
                    )
                    break  # Only one zone should be active at a time
            except Exception as e:
                print(f"Warning: Could not get switch state for {zone.switch_entity}: {e}")
    
    # Queue length - placeholder until queue processor is implemented (task 11)
    # For now, return 0 as the queue processor doesn't exist yet
    queue_length = 0
    
    return PumpStatusResponse(
        pump_id=pump.id,
        pump_name=pump.name,
        lock_entity=pump.lock_entity,
        is_locked=is_locked,
        enabled=pump.enabled,
        active_zone=active_zone,
        queue_length=queue_length
    )
