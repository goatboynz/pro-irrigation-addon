"""
Global Settings API Endpoints

This module implements endpoints for managing global irrigation system settings
that apply to all zones in auto mode.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.global_settings import GlobalSettings
from ..models.schemas import GlobalSettingsUpdate, GlobalSettingsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=GlobalSettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Get global settings.
    
    Returns the current global settings configuration. If no settings exist,
    creates a default settings row with all fields set to None.
    
    Args:
        db: Database session (injected)
    
    Returns:
        GlobalSettingsResponse: Global settings information
    """
    try:
        # Get settings (should only be one row)
        settings = db.query(GlobalSettings).first()
        
        # Create default settings if none exist
        if not settings:
            logger.info("No global settings found, creating default settings")
            settings = GlobalSettings(
                lights_on_entity=None,
                lights_off_entity=None,
                p1_delay_entity=None,
                p2_delay_entity=None,
                p2_buffer_entity=None,
                feed_notes=None
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        logger.debug("Retrieved global settings")
        return settings
    
    except Exception as e:
        logger.error(f"Error retrieving global settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve global settings: {str(e)}"
        )


@router.put("", response_model=GlobalSettingsResponse)
async def update_settings(
    settings_data: GlobalSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update global settings.
    
    Updates the global settings configuration. Only provided fields will be updated.
    If no settings exist, creates a new settings row.
    
    Args:
        settings_data: Settings update data
        db: Database session (injected)
    
    Returns:
        GlobalSettingsResponse: Updated global settings information
    """
    try:
        # Get existing settings or create new
        settings = db.query(GlobalSettings).first()
        
        if not settings:
            logger.info("No global settings found, creating new settings")
            settings = GlobalSettings()
            db.add(settings)
        
        # Update fields if provided
        if settings_data.lights_on_entity is not None:
            settings.lights_on_entity = settings_data.lights_on_entity
        
        if settings_data.lights_off_entity is not None:
            settings.lights_off_entity = settings_data.lights_off_entity
        
        if settings_data.p1_delay_entity is not None:
            settings.p1_delay_entity = settings_data.p1_delay_entity
        
        if settings_data.p2_delay_entity is not None:
            settings.p2_delay_entity = settings_data.p2_delay_entity
        
        if settings_data.p2_buffer_entity is not None:
            settings.p2_buffer_entity = settings_data.p2_buffer_entity
        
        if settings_data.feed_notes is not None:
            settings.feed_notes = settings_data.feed_notes
        
        db.commit()
        db.refresh(settings)
        
        logger.info("Updated global settings")
        return settings
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating global settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update global settings: {str(e)}"
        )
