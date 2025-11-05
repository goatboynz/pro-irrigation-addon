"""
Settings API router for v2 room-based irrigation system.

This module provides endpoints for managing system settings:
- GET /api/settings - Get system settings
- PUT /api/settings - Update system settings
- POST /api/system/reset - Delete all data except settings
- GET /api/system/health - System health check
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.models.database import get_db
from backend.models.v2_settings import SystemSettings
from backend.models.v2_room import Room
from backend.models.v2_pump import PumpV2
from backend.models.v2_zone import ZoneV2
from backend.models.v2_water_event import WaterEvent
from backend.models.v2_sensor import EnvironmentalSensor
from backend.schemas import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(prefix="/api", tags=["Settings"])


@router.get("/settings", response_model=SystemSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """
    Get system settings.
    
    Returns the singleton SystemSettings record (id=1).
    
    Args:
        db: Database session
        
    Returns:
        SystemSettingsResponse: Current system settings
        
    Raises:
        HTTPException: 404 if settings not found (should never happen)
    """
    settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System settings not found. Database may not be initialized properly."
        )
    
    return settings


@router.put("/settings", response_model=SystemSettingsResponse)
def update_settings(
    settings_data: SystemSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update system settings.
    
    Updates the singleton SystemSettings record (id=1).
    
    Args:
        settings_data: New settings values
        db: Database session
        
    Returns:
        SystemSettingsResponse: Updated system settings
        
    Raises:
        HTTPException: 404 if settings not found
        HTTPException: 400 if validation fails
    """
    settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System settings not found. Database may not be initialized properly."
        )
    
    # Validate settings values
    if settings_data.pump_startup_delay_seconds < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pump_startup_delay_seconds must be >= 0"
        )
    
    if settings_data.zone_switch_delay_seconds < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="zone_switch_delay_seconds must be >= 0"
        )
    
    if settings_data.scheduler_interval_seconds < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduler_interval_seconds must be >= 1"
        )
    
    # Update settings
    settings.pump_startup_delay_seconds = settings_data.pump_startup_delay_seconds
    settings.zone_switch_delay_seconds = settings_data.zone_switch_delay_seconds
    settings.scheduler_interval_seconds = settings_data.scheduler_interval_seconds
    
    db.commit()
    db.refresh(settings)
    
    return settings


# ============================================================================
# System Management Endpoints
# ============================================================================

@router.post("/system/reset", status_code=status.HTTP_200_OK)
def reset_system(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Delete all data except system settings.
    
    This endpoint removes:
    - All rooms (cascade deletes pumps, zones, events, sensors)
    - All pumps (cascade deletes zones)
    - All zones
    - All water events
    - All environmental sensors
    
    System settings (id=1) are preserved.
    
    Args:
        db: Database session
        
    Returns:
        dict: Summary of deleted records
    """
    # Count records before deletion
    rooms_count = db.query(Room).count()
    pumps_count = db.query(PumpV2).count()
    zones_count = db.query(ZoneV2).count()
    events_count = db.query(WaterEvent).count()
    sensors_count = db.query(EnvironmentalSensor).count()
    
    # Delete all rooms (cascade will handle related entities)
    db.query(Room).delete()
    
    # Commit the transaction
    db.commit()
    
    return {
        "status": "success",
        "message": "All data deleted except system settings",
        "deleted": {
            "rooms": rooms_count,
            "pumps": pumps_count,
            "zones": zones_count,
            "water_events": events_count,
            "sensors": sensors_count
        }
    }


@router.get("/system/health", status_code=status.HTTP_200_OK)
def system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    System health check with detailed status.
    
    Provides information about:
    - Database connectivity
    - System settings status
    - Entity counts
    
    Args:
        db: Database session
        
    Returns:
        dict: System health information
    """
    try:
        # Check database connectivity
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        
        if not settings:
            return {
                "status": "unhealthy",
                "database": "connected",
                "settings": "missing",
                "message": "System settings not initialized"
            }
        
        # Count entities
        rooms_count = db.query(Room).count()
        pumps_count = db.query(PumpV2).count()
        zones_count = db.query(ZoneV2).count()
        events_count = db.query(WaterEvent).count()
        sensors_count = db.query(EnvironmentalSensor).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "settings": "initialized",
            "entities": {
                "rooms": rooms_count,
                "pumps": pumps_count,
                "zones": zones_count,
                "water_events": events_count,
                "sensors": sensors_count
            },
            "configuration": {
                "pump_startup_delay_seconds": settings.pump_startup_delay_seconds,
                "zone_switch_delay_seconds": settings.zone_switch_delay_seconds,
                "scheduler_interval_seconds": settings.scheduler_interval_seconds
            }
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "message": str(e)
        }
