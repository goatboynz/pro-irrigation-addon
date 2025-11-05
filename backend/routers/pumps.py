"""
Pump API Endpoints

This module implements all REST API endpoints for pump management,
including CRUD operations and real-time status monitoring.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.pump import Pump
from ..models.schemas import PumpCreate, PumpUpdate, PumpResponse, PumpBasic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pumps", tags=["Pumps"])

# Global reference to queue processor (will be set by main application)
_queue_processor = None


def set_queue_processor(processor):
    """
    Set the global queue processor reference.
    
    This function should be called by the main application to provide
    access to the queue processor for status checks.
    
    Args:
        processor: QueueProcessor instance
    """
    global _queue_processor
    _queue_processor = processor


def get_queue_processor():
    """
    Get the queue processor instance.
    
    Returns:
        QueueProcessor instance or None if not initialized
    """
    return _queue_processor


@router.get("", response_model=List[PumpResponse])
async def list_pumps(db: Session = Depends(get_db)):
    """
    List all pumps with status information.
    
    Returns a list of all configured pumps including their current status
    (idle, running, or queued), active zone name if running, and queue length.
    
    Args:
        db: Database session (injected)
    
    Returns:
        List[PumpResponse]: List of pumps with status
    """
    try:
        pumps = db.query(Pump).all()
        
        # Get queue processor for status information
        queue_processor = get_queue_processor()
        
        pump_responses = []
        for pump in pumps:
            # Get status from queue processor if available
            if queue_processor:
                status_info = queue_processor.get_pump_status(pump.id)
            else:
                # Default status if queue processor not available
                status_info = {
                    'status': 'idle',
                    'active_zone': None,
                    'queue_length': 0
                }
            
            pump_response = PumpResponse(
                id=pump.id,
                name=pump.name,
                lock_entity=pump.lock_entity,
                status=status_info['status'],
                active_zone=status_info['active_zone'],
                queue_length=status_info['queue_length'],
                created_at=pump.created_at,
                updated_at=pump.updated_at
            )
            pump_responses.append(pump_response)
        
        logger.info(f"Listed {len(pump_responses)} pumps")
        return pump_responses
    
    except Exception as e:
        logger.error(f"Error listing pumps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pumps: {str(e)}"
        )


@router.post("", response_model=PumpBasic, status_code=status.HTTP_201_CREATED)
async def create_pump(pump_data: PumpCreate, db: Session = Depends(get_db)):
    """
    Create a new pump.
    
    Creates a new pump configuration with the specified name and lock entity.
    The lock entity must be a valid Home Assistant entity ID.
    
    Args:
        pump_data: Pump creation data
        db: Database session (injected)
    
    Returns:
        PumpBasic: Created pump information
    
    Raises:
        HTTPException: If pump creation fails
    """
    try:
        # Create new pump
        new_pump = Pump(
            name=pump_data.name,
            lock_entity=pump_data.lock_entity
        )
        
        db.add(new_pump)
        db.commit()
        db.refresh(new_pump)
        
        logger.info(f"Created pump: {new_pump.id} ({new_pump.name})")
        return new_pump
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating pump: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pump: {str(e)}"
        )


@router.get("/{pump_id}", response_model=PumpBasic)
async def get_pump(pump_id: int, db: Session = Depends(get_db)):
    """
    Get pump details by ID.
    
    Returns detailed information about a specific pump.
    
    Args:
        pump_id: Pump ID
        db: Database session (injected)
    
    Returns:
        PumpBasic: Pump information
    
    Raises:
        HTTPException: If pump not found
    """
    try:
        pump = db.query(Pump).filter(Pump.id == pump_id).first()
        
        if not pump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pump with ID {pump_id} not found"
            )
        
        logger.debug(f"Retrieved pump: {pump.id} ({pump.name})")
        return pump
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pump: {str(e)}"
        )


@router.put("/{pump_id}", response_model=PumpBasic)
async def update_pump(
    pump_id: int,
    pump_data: PumpUpdate,
    db: Session = Depends(get_db)
):
    """
    Update pump configuration.
    
    Updates the name and/or lock entity of an existing pump.
    Only provided fields will be updated.
    
    Args:
        pump_id: Pump ID
        pump_data: Pump update data
        db: Database session (injected)
    
    Returns:
        PumpBasic: Updated pump information
    
    Raises:
        HTTPException: If pump not found or update fails
    """
    try:
        pump = db.query(Pump).filter(Pump.id == pump_id).first()
        
        if not pump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pump with ID {pump_id} not found"
            )
        
        # Update fields if provided
        if pump_data.name is not None:
            pump.name = pump_data.name
        
        if pump_data.lock_entity is not None:
            pump.lock_entity = pump_data.lock_entity
        
        db.commit()
        db.refresh(pump)
        
        logger.info(f"Updated pump: {pump.id} ({pump.name})")
        return pump
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pump: {str(e)}"
        )


@router.delete("/{pump_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pump(pump_id: int, db: Session = Depends(get_db)):
    """
    Delete a pump.
    
    Deletes a pump and all its associated zones (cascade delete).
    This operation cannot be undone.
    
    Args:
        pump_id: Pump ID
        db: Database session (injected)
    
    Raises:
        HTTPException: If pump not found or deletion fails
    """
    try:
        pump = db.query(Pump).filter(Pump.id == pump_id).first()
        
        if not pump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pump with ID {pump_id} not found"
            )
        
        pump_name = pump.name
        db.delete(pump)
        db.commit()
        
        logger.info(f"Deleted pump: {pump_id} ({pump_name})")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pump: {str(e)}"
        )


@router.get("/{pump_id}/status", response_model=dict)
async def get_pump_status(pump_id: int, db: Session = Depends(get_db)):
    """
    Get real-time pump status.
    
    Returns the current status of a pump including whether it's idle,
    running a zone, or has jobs queued. Also includes the active zone
    name if running and the number of jobs in the queue.
    
    Args:
        pump_id: Pump ID
        db: Database session (injected)
    
    Returns:
        dict: Pump status information with keys:
            - status: 'idle', 'running', or 'queued'
            - active_zone: Name of active zone if running, None otherwise
            - queue_length: Number of jobs in queue
    
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
        
        # Get status from queue processor
        queue_processor = get_queue_processor()
        
        if queue_processor:
            status_info = queue_processor.get_pump_status(pump_id)
        else:
            # Default status if queue processor not available
            status_info = {
                'status': 'idle',
                'active_zone': None,
                'queue_length': 0
            }
        
        logger.debug(f"Retrieved status for pump {pump_id}: {status_info['status']}")
        return status_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for pump {pump_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pump status: {str(e)}"
        )
