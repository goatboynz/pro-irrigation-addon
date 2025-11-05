"""
Zones API router for v2 room-based irrigation system.

This module provides CRUD endpoints for managing zones:
- GET /api/pumps/{pump_id}/zones - List zones for pump
- POST /api/pumps/{pump_id}/zones - Create zone
- PUT /api/zones/{id} - Update zone
- DELETE /api/zones/{id} - Delete zone
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models.database import get_db
from backend.models.v2_pump import PumpV2
from backend.models.v2_zone import ZoneV2
from backend.schemas import (
    ZoneCreate,
    ZoneUpdate,
    ZoneResponse
)

router = APIRouter(prefix="/api", tags=["Zones"])


@router.get("/pumps/{pump_id}/zones", response_model=List[ZoneResponse])
def list_zones_for_pump(pump_id: int, db: Session = Depends(get_db)):
    """
    List all zones for a specific pump.
    
    Args:
        pump_id: Pump ID
        db: Database session
        
    Returns:
        List[ZoneResponse]: List of zones for the pump
        
    Raises:
        HTTPException: 404 if pump not found
    """
    # Verify pump exists
    pump = db.query(PumpV2).filter(PumpV2.id == pump_id).first()
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {pump_id} not found"
        )
    
    # Get all zones for the pump
    zones = db.query(ZoneV2).filter(ZoneV2.pump_id == pump_id).all()
    return zones


@router.post("/pumps/{pump_id}/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(pump_id: int, zone_data: ZoneCreate, db: Session = Depends(get_db)):
    """
    Create a new zone for a pump.
    
    Args:
        pump_id: Pump ID
        zone_data: Zone creation data
        db: Database session
        
    Returns:
        ZoneResponse: Created zone
        
    Raises:
        HTTPException: 404 if pump not found
        HTTPException: 400 if zone name already exists for this pump
    """
    # Verify pump exists
    pump = db.query(PumpV2).filter(PumpV2.id == pump_id).first()
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {pump_id} not found"
        )
    
    # Check if zone with same name already exists for this pump
    existing_zone = db.query(ZoneV2).filter(
        ZoneV2.pump_id == pump_id,
        ZoneV2.name == zone_data.name
    ).first()
    if existing_zone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone with name '{zone_data.name}' already exists for this pump"
        )
    
    # Create new zone
    new_zone = ZoneV2(
        pump_id=pump_id,
        name=zone_data.name,
        switch_entity=zone_data.switch_entity,
        enabled=zone_data.enabled
    )
    
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    
    return new_zone


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: int, zone_data: ZoneUpdate, db: Session = Depends(get_db)):
    """
    Update an existing zone.
    
    Args:
        zone_id: Zone ID
        zone_data: Zone update data
        db: Database session
        
    Returns:
        ZoneResponse: Updated zone
        
    Raises:
        HTTPException: 404 if zone not found
        HTTPException: 400 if new name conflicts with existing zone for same pump
    """
    zone = db.query(ZoneV2).filter(ZoneV2.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with id {zone_id} not found"
        )
    
    # Check if new name conflicts with existing zone for same pump
    if zone_data.name is not None and zone_data.name != zone.name:
        existing_zone = db.query(ZoneV2).filter(
            ZoneV2.pump_id == zone.pump_id,
            ZoneV2.name == zone_data.name
        ).first()
        if existing_zone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Zone with name '{zone_data.name}' already exists for this pump"
            )
    
    # Update fields if provided
    update_data = zone_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    
    db.commit()
    db.refresh(zone)
    
    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    """
    Delete a zone.
    
    This will remove the zone and its associations with water events.
    
    Args:
        zone_id: Zone ID
        db: Database session
        
    Raises:
        HTTPException: 404 if zone not found
    """
    zone = db.query(ZoneV2).filter(ZoneV2.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with id {zone_id} not found"
        )
    
    db.delete(zone)
    db.commit()
    
    return None
