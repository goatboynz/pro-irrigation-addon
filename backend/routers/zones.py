"""
Zone API Endpoints

This module implements all REST API endpoints for zone management,
including CRUD operations and next run time calculation.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.pump import Pump
from ..models.zone import Zone
from ..models.schemas import (
    ZoneCreate,
    ZoneUpdate,
    ZoneResponse,
    ZoneBasic,
    NextRunResponse
)
from ..services.calculator import get_next_run_time, ScheduleCalculationError, ManualScheduleParseError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Zones"])

# Global reference to HA client and global settings getter (will be set by main application)
_ha_client = None
_global_settings_getter = None


def set_ha_client(client):
    """
    Set the global Home Assistant client reference.
    
    Args:
        client: HomeAssistantClient instance
    """
    global _ha_client
    _ha_client = client


def set_global_settings_getter(getter_func):
    """
    Set the global settings getter function.
    
    Args:
        getter_func: Function that returns GlobalTimingSettings
    """
    global _global_settings_getter
    _global_settings_getter = getter_func


def get_ha_client():
    """Get the Home Assistant client instance."""
    return _ha_client


def get_global_settings_getter():
    """Get the global settings getter function."""
    return _global_settings_getter


@router.get("/api/pumps/{pump_id}/zones", response_model=List[ZoneBasic])
async def list_zones(pump_id: int, db: Session = Depends(get_db)):
    """
    List all zones for a specific pump.
    
    Returns a list of all zones configured for the specified pump.
    
    Args:
        pump_id: Pump ID
        db: Database session (injected)
    
    Returns:
        List[ZoneBasic]: List of zones
    
    Raises:
        HTTPException: If pump not found
    """
    try:
        # Verify pump exists
        pump = db.query(Pump).filter(Pump.id == pump_id).first()
        
        if not pump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pump with ID {pump_id} not found"
            )
        
        # Get zones for this pump
        zones = db.query(Zone).filter(Zone.pump_id == pump_id).all()
        
        logger.info(f"Listed {len(zones)} zones for pump {pump_id}")
        return zones
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing zones for pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list zones: {str(e)}"
        )


@router.post("/api/pumps/{pump_id}/zones", response_model=ZoneBasic, status_code=status.HTTP_201_CREATED)
async def create_zone(
    pump_id: int,
    zone_data: ZoneCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new zone for a pump.
    
    Creates a new irrigation zone with the specified configuration.
    The zone can be configured in either auto or manual mode.
    
    Args:
        pump_id: Pump ID
        zone_data: Zone creation data
        db: Database session (injected)
    
    Returns:
        ZoneBasic: Created zone information
    
    Raises:
        HTTPException: If pump not found or zone creation fails
    """
    try:
        # Verify pump exists
        pump = db.query(Pump).filter(Pump.id == pump_id).first()
        
        if not pump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pump with ID {pump_id} not found"
            )
        
        # Create new zone
        new_zone = Zone(
            pump_id=pump_id,
            name=zone_data.name,
            switch_entity=zone_data.switch_entity,
            mode=zone_data.mode,
            p1_duration_sec=zone_data.p1_duration_sec,
            p2_event_count=zone_data.p2_event_count,
            p2_duration_sec=zone_data.p2_duration_sec,
            p1_manual_list=zone_data.p1_manual_list,
            p2_manual_list=zone_data.p2_manual_list,
            enabled=zone_data.enabled
        )
        
        db.add(new_zone)
        db.commit()
        db.refresh(new_zone)
        
        logger.info(f"Created zone: {new_zone.id} ({new_zone.name}) for pump {pump_id}")
        return new_zone
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating zone for pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create zone: {str(e)}"
        )


@router.get("/api/zones/{zone_id}", response_model=ZoneBasic)
async def get_zone(zone_id: int, db: Session = Depends(get_db)):
    """
    Get zone details by ID.
    
    Returns detailed information about a specific zone.
    
    Args:
        zone_id: Zone ID
        db: Database session (injected)
    
    Returns:
        ZoneBasic: Zone information
    
    Raises:
        HTTPException: If zone not found
    """
    try:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone with ID {zone_id} not found"
            )
        
        logger.debug(f"Retrieved zone: {zone.id} ({zone.name})")
        return zone
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving zone {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve zone: {str(e)}"
        )


@router.put("/api/zones/{zone_id}", response_model=ZoneBasic)
async def update_zone(
    zone_id: int,
    zone_data: ZoneUpdate,
    db: Session = Depends(get_db)
):
    """
    Update zone configuration.
    
    Updates the configuration of an existing zone.
    Only provided fields will be updated.
    
    Args:
        zone_id: Zone ID
        zone_data: Zone update data
        db: Database session (injected)
    
    Returns:
        ZoneBasic: Updated zone information
    
    Raises:
        HTTPException: If zone not found or update fails
    """
    try:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone with ID {zone_id} not found"
            )
        
        # Update fields if provided
        if zone_data.name is not None:
            zone.name = zone_data.name
        
        if zone_data.switch_entity is not None:
            zone.switch_entity = zone_data.switch_entity
        
        if zone_data.mode is not None:
            zone.mode = zone_data.mode
        
        if zone_data.p1_duration_sec is not None:
            zone.p1_duration_sec = zone_data.p1_duration_sec
        
        if zone_data.p2_event_count is not None:
            zone.p2_event_count = zone_data.p2_event_count
        
        if zone_data.p2_duration_sec is not None:
            zone.p2_duration_sec = zone_data.p2_duration_sec
        
        if zone_data.p1_manual_list is not None:
            zone.p1_manual_list = zone_data.p1_manual_list
        
        if zone_data.p2_manual_list is not None:
            zone.p2_manual_list = zone_data.p2_manual_list
        
        if zone_data.enabled is not None:
            zone.enabled = zone_data.enabled
        
        db.commit()
        db.refresh(zone)
        
        logger.info(f"Updated zone: {zone.id} ({zone.name})")
        return zone
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating zone {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update zone: {str(e)}"
        )


@router.delete("/api/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    """
    Delete a zone.
    
    Deletes a zone configuration. This operation cannot be undone.
    
    Args:
        zone_id: Zone ID
        db: Database session (injected)
    
    Raises:
        HTTPException: If zone not found or deletion fails
    """
    try:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone with ID {zone_id} not found"
            )
        
        zone_name = zone.name
        db.delete(zone)
        db.commit()
        
        logger.info(f"Deleted zone: {zone_id} ({zone_name})")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting zone {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete zone: {str(e)}"
        )


@router.get("/api/zones/{zone_id}/next-run", response_model=NextRunResponse)
async def get_zone_next_run(zone_id: int, db: Session = Depends(get_db)):
    """
    Get the next scheduled run time for a zone.
    
    Calculates and returns the next scheduled irrigation event for the zone
    based on its configuration (auto or manual mode) and global settings.
    
    Args:
        zone_id: Zone ID
        db: Database session (injected)
    
    Returns:
        NextRunResponse: Next run time information
    
    Raises:
        HTTPException: If zone not found or calculation fails
    """
    try:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone with ID {zone_id} not found"
            )
        
        # Get global settings if zone is in auto mode
        global_settings = None
        if zone.mode == 'auto':
            settings_getter = get_global_settings_getter()
            if settings_getter:
                try:
                    global_settings = settings_getter()
                except Exception as e:
                    logger.warning(f"Failed to get global settings: {str(e)}")
                    # Continue without global settings - will return None for next run
        
        # Calculate next run time
        try:
            next_run = get_next_run_time(zone, global_settings)
            
            logger.debug(f"Calculated next run for zone {zone_id}: {next_run}")
            
            return NextRunResponse(
                zone_id=zone.id,
                zone_name=zone.name,
                next_run=next_run
            )
        
        except (ScheduleCalculationError, ManualScheduleParseError) as e:
            logger.error(f"Error calculating next run for zone {zone_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to calculate next run time: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next run for zone {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next run time: {str(e)}"
        )
