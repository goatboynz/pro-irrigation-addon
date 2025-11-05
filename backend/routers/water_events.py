"""
Water Events API router for v2 room-based irrigation system.

This module provides CRUD endpoints for managing water events:
- GET /api/rooms/{room_id}/events - List events for room
- POST /api/rooms/{room_id}/events - Create P1 or P2 event
- PUT /api/events/{id} - Update event
- DELETE /api/events/{id} - Delete event
- POST /api/events/{id}/zones/{zone_id} - Assign zone to event
- DELETE /api/events/{id}/zones/{zone_id} - Remove zone from event
- GET /api/events/{id}/next-run - Calculate next scheduled time
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from backend.models.database import get_db
from backend.models.v2_water_event import WaterEvent
from backend.models.v2_room import Room
from backend.models.v2_zone import ZoneV2
from backend.schemas import (
    WaterEventCreate,
    WaterEventUpdate,
    WaterEventResponse,
    WaterEventDetailResponse
)

router = APIRouter(tags=["Water Events"])


@router.get("/api/rooms/{room_id}/events", response_model=List[WaterEventDetailResponse])
def list_events_for_room(room_id: int, db: Session = Depends(get_db)):
    """
    List all water events for a specific room.
    
    Args:
        room_id: Room ID
        db: Database session
        
    Returns:
        List[WaterEventDetailResponse]: List of water events with assigned zones
        
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
    
    # Get all events for this room
    events = db.query(WaterEvent).filter(WaterEvent.room_id == room_id).all()
    return events


@router.post("/api/rooms/{room_id}/events", response_model=WaterEventDetailResponse, status_code=status.HTTP_201_CREATED)
def create_event(room_id: int, event_data: WaterEventCreate, db: Session = Depends(get_db)):
    """
    Create a new water event (P1 or P2) for a room.
    
    P1 events require delay_minutes and trigger after lights-on.
    P2 events require time_of_day in HH:MM format.
    
    Args:
        room_id: Room ID
        event_data: Water event creation data
        db: Database session
        
    Returns:
        WaterEventDetailResponse: Created water event with assigned zones
        
    Raises:
        HTTPException: 404 if room not found
        HTTPException: 400 if zone IDs are invalid
    """
    # Verify room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found"
        )
    
    # Create new water event
    new_event = WaterEvent(
        room_id=room_id,
        event_type=event_data.event_type,
        name=event_data.name,
        delay_minutes=event_data.delay_minutes,
        time_of_day=event_data.time_of_day,
        run_time_seconds=event_data.run_time_seconds,
        enabled=event_data.enabled
    )
    
    db.add(new_event)
    db.flush()  # Flush to get the event ID before assigning zones
    
    # Assign zones if provided
    if event_data.zone_ids:
        zones = db.query(ZoneV2).filter(ZoneV2.id.in_(event_data.zone_ids)).all()
        
        # Verify all zone IDs are valid
        if len(zones) != len(event_data.zone_ids):
            found_ids = {z.id for z in zones}
            missing_ids = set(event_data.zone_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Zone IDs not found: {missing_ids}"
            )
        
        new_event.zones = zones
    
    db.commit()
    db.refresh(new_event)
    
    return new_event


@router.put("/api/events/{event_id}", response_model=WaterEventDetailResponse)
def update_event(event_id: int, event_data: WaterEventUpdate, db: Session = Depends(get_db)):
    """
    Update an existing water event.
    
    Args:
        event_id: Water event ID
        event_data: Water event update data
        db: Database session
        
    Returns:
        WaterEventDetailResponse: Updated water event
        
    Raises:
        HTTPException: 404 if event not found
    """
    event = db.query(WaterEvent).filter(WaterEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water event with id {event_id} not found"
        )
    
    # Update fields if provided
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """
    Delete a water event.
    
    This will also remove all zone assignments for this event.
    
    Args:
        event_id: Water event ID
        db: Database session
        
    Raises:
        HTTPException: 404 if event not found
    """
    event = db.query(WaterEvent).filter(WaterEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water event with id {event_id} not found"
        )
    
    db.delete(event)
    db.commit()
    
    return None



# ============================================================================
# Zone Assignment Endpoints
# ============================================================================

@router.post("/api/events/{event_id}/zones/{zone_id}", response_model=WaterEventDetailResponse)
def assign_zone_to_event(event_id: int, zone_id: int, db: Session = Depends(get_db)):
    """
    Assign a zone to a water event.
    
    This creates a many-to-many relationship between the event and zone.
    A zone can be assigned to multiple events, and an event can have multiple zones.
    
    Args:
        event_id: Water event ID
        zone_id: Zone ID
        db: Database session
        
    Returns:
        WaterEventDetailResponse: Updated water event with all assigned zones
        
    Raises:
        HTTPException: 404 if event or zone not found
        HTTPException: 400 if zone is already assigned to this event
    """
    # Verify event exists
    event = db.query(WaterEvent).filter(WaterEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water event with id {event_id} not found"
        )
    
    # Verify zone exists
    zone = db.query(ZoneV2).filter(ZoneV2.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with id {zone_id} not found"
        )
    
    # Check if zone is already assigned to this event
    if zone in event.zones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone {zone_id} is already assigned to event {event_id}"
        )
    
    # Assign zone to event
    event.zones.append(zone)
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/api/events/{event_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_zone_from_event(event_id: int, zone_id: int, db: Session = Depends(get_db)):
    """
    Remove a zone from a water event.
    
    This removes the many-to-many relationship between the event and zone.
    
    Args:
        event_id: Water event ID
        zone_id: Zone ID
        db: Database session
        
    Raises:
        HTTPException: 404 if event or zone not found
        HTTPException: 400 if zone is not assigned to this event
    """
    # Verify event exists
    event = db.query(WaterEvent).filter(WaterEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water event with id {event_id} not found"
        )
    
    # Verify zone exists
    zone = db.query(ZoneV2).filter(ZoneV2.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with id {zone_id} not found"
        )
    
    # Check if zone is assigned to this event
    if zone not in event.zones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone {zone_id} is not assigned to event {event_id}"
        )
    
    # Remove zone from event
    event.zones.remove(zone)
    db.commit()
    
    return None



# ============================================================================
# Next Run Calculation Endpoint
# ============================================================================

from pydantic import BaseModel
from backend.services.ha_client import get_ha_client


class NextRunResponse(BaseModel):
    """Schema for next run calculation response."""
    event_id: int
    event_name: str
    event_type: str
    next_run_time: Optional[str]
    calculation_details: str


@router.get("/api/events/{event_id}/next-run", response_model=NextRunResponse)
async def calculate_next_run(event_id: int, db: Session = Depends(get_db)):
    """
    Calculate the next scheduled run time for a water event.
    
    For P1 events:
        - Queries the room's lights_on_entity from Home Assistant
        - Adds delay_minutes to get the scheduled time
        - Returns next occurrence (today if not yet passed, tomorrow otherwise)
    
    For P2 events:
        - Uses the time_of_day field (HH:MM format)
        - Returns next occurrence (today if not yet passed, tomorrow otherwise)
    
    Args:
        event_id: Water event ID
        db: Database session
        
    Returns:
        NextRunResponse: Next run time and calculation details
        
    Raises:
        HTTPException: 404 if event not found
        HTTPException: 400 if event is disabled or missing required data
    """
    # Get event
    event = db.query(WaterEvent).filter(WaterEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water event with id {event_id} not found"
        )
    
    # Check if event is enabled
    if not event.enabled:
        return NextRunResponse(
            event_id=event.id,
            event_name=event.name,
            event_type=event.event_type,
            next_run_time=None,
            calculation_details="Event is disabled"
        )
    
    # Get current time
    now = datetime.now()
    
    if event.event_type == "p1":
        # P1 event: Calculate based on lights_on_entity + delay_minutes
        room = db.query(Room).filter(Room.id == event.room_id).first()
        
        if not room or not room.lights_on_entity:
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=None,
                calculation_details="Room lights_on_entity not configured"
            )
        
        if event.delay_minutes is None:
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=None,
                calculation_details="P1 event missing delay_minutes"
            )
        
        # Get lights_on time from Home Assistant
        ha_client = get_ha_client()
        try:
            lights_on_state = await ha_client.get_state(room.lights_on_entity)
            lights_on_time_str = lights_on_state.state
            
            # Parse the time (format: HH:MM:SS or HH:MM)
            time_parts = lights_on_time_str.split(":")
            if len(time_parts) >= 2:
                lights_on_hour = int(time_parts[0])
                lights_on_minute = int(time_parts[1])
                
                # Calculate event time
                event_time = now.replace(hour=lights_on_hour, minute=lights_on_minute, second=0, microsecond=0)
                event_time += timedelta(minutes=event.delay_minutes)
                
                # If the time has passed today, schedule for tomorrow
                if event_time <= now:
                    event_time += timedelta(days=1)
                
                return NextRunResponse(
                    event_id=event.id,
                    event_name=event.name,
                    event_type=event.event_type,
                    next_run_time=event_time.isoformat(),
                    calculation_details=f"Lights on at {lights_on_time_str}, event runs {event.delay_minutes} minutes later"
                )
            else:
                return NextRunResponse(
                    event_id=event.id,
                    event_name=event.name,
                    event_type=event.event_type,
                    next_run_time=None,
                    calculation_details=f"Invalid lights_on time format: {lights_on_time_str}"
                )
                
        except Exception as e:
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=None,
                calculation_details=f"Error querying Home Assistant: {str(e)}"
            )
    
    elif event.event_type == "p2":
        # P2 event: Calculate based on time_of_day
        if not event.time_of_day:
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=None,
                calculation_details="P2 event missing time_of_day"
            )
        
        # Parse time_of_day (HH:MM format)
        try:
            time_parts = event.time_of_day.split(":")
            event_hour = int(time_parts[0])
            event_minute = int(time_parts[1])
            
            # Calculate event time for today
            event_time = now.replace(hour=event_hour, minute=event_minute, second=0, microsecond=0)
            
            # If the time has passed today, schedule for tomorrow
            if event_time <= now:
                event_time += timedelta(days=1)
            
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=event_time.isoformat(),
                calculation_details=f"Scheduled for {event.time_of_day} daily"
            )
            
        except Exception as e:
            return NextRunResponse(
                event_id=event.id,
                event_name=event.name,
                event_type=event.event_type,
                next_run_time=None,
                calculation_details=f"Error parsing time_of_day: {str(e)}"
            )
    
    else:
        return NextRunResponse(
            event_id=event.id,
            event_name=event.name,
            event_type=event.event_type,
            next_run_time=None,
            calculation_details=f"Unknown event type: {event.event_type}"
        )
