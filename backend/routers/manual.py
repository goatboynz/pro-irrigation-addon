"""
Manual control API router for v2 room-based irrigation system.

This module provides endpoints for manual zone control:
- POST /api/manual/run - Run zone manually with custom duration
- POST /api/manual/stop - Emergency stop current operation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from backend.models.database import get_db
from backend.models.v2_zone import ZoneV2
from backend.models.v2_pump import PumpV2
from backend.services.queue_processor import get_queue_processor, ExecutionJob

router = APIRouter(prefix="/api/manual", tags=["Manual Control"])


class ManualRunRequest(BaseModel):
    """Request schema for manual zone run."""
    zone_id: int = Field(..., description="Zone ID to run")
    duration_seconds: int = Field(..., gt=0, description="Duration in seconds")


class ManualRunResponse(BaseModel):
    """Response schema for manual zone run."""
    message: str
    zone_id: int
    zone_name: str
    pump_id: int
    pump_name: str
    duration_seconds: int
    queue_position: int
    scheduled_time: datetime


class ManualStopRequest(BaseModel):
    """Request schema for emergency stop."""
    pump_id: int = Field(..., description="Pump ID to stop")


class ManualStopResponse(BaseModel):
    """Response schema for emergency stop."""
    message: str
    pump_id: int
    pump_name: str
    stopped_job: Optional[str] = None
    cleared_jobs: int


@router.post("/run", response_model=ManualRunResponse, status_code=status.HTTP_202_ACCEPTED)
def run_zone_manually(
    request: ManualRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run a zone manually with custom duration.
    
    This endpoint creates a manual execution job and adds it directly to the
    pump's queue, bypassing the scheduler. The job will be executed as soon
    as the pump is available.
    
    Args:
        request: Manual run request with zone_id and duration
        db: Database session
        
    Returns:
        ManualRunResponse: Information about the queued job
        
    Raises:
        HTTPException: 404 if zone not found
        HTTPException: 400 if zone or pump is disabled
    """
    # Get zone from database
    zone = db.query(ZoneV2).filter(ZoneV2.id == request.zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with id {request.zone_id} not found"
        )
    
    # Check if zone is enabled
    if not zone.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone '{zone.name}' is disabled"
        )
    
    # Get pump from database
    pump = db.query(PumpV2).filter(PumpV2.id == zone.pump_id).first()
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {zone.pump_id} not found"
        )
    
    # Check if pump is enabled
    if not pump.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pump '{pump.name}' is disabled"
        )
    
    # Create execution job
    job = ExecutionJob(
        zone_id=zone.id,
        zone_name=f"{zone.name} (Manual)",
        switch_entity=zone.switch_entity,
        duration_seconds=request.duration_seconds,
        scheduled_time=datetime.utcnow()
    )
    
    # Add job to pump queue
    queue_processor = get_queue_processor()
    queue_processor.add_job(pump.id, job)
    
    # Get queue position (length after adding)
    queue_position = queue_processor.get_queue_length(pump.id)
    
    return ManualRunResponse(
        message=f"Manual run queued for zone '{zone.name}'",
        zone_id=zone.id,
        zone_name=zone.name,
        pump_id=pump.id,
        pump_name=pump.name,
        duration_seconds=request.duration_seconds,
        queue_position=queue_position,
        scheduled_time=job.scheduled_time
    )


@router.post("/stop", response_model=ManualStopResponse)
def emergency_stop(
    request: ManualStopRequest,
    db: Session = Depends(get_db)
):
    """
    Emergency stop for a pump.
    
    This endpoint clears all jobs from a pump's queue. If a job is currently
    executing, it will continue to completion (as stopping mid-execution could
    leave equipment in an unsafe state), but no further jobs will run.
    
    Note: This does not forcibly stop the currently executing job. The job
    will complete its normal shutdown sequence to ensure proper cleanup.
    
    Args:
        request: Emergency stop request with pump_id
        db: Database session
        
    Returns:
        ManualStopResponse: Information about stopped operations
        
    Raises:
        HTTPException: 404 if pump not found
    """
    # Get pump from database
    pump = db.query(PumpV2).filter(PumpV2.id == request.pump_id).first()
    if not pump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pump with id {request.pump_id} not found"
        )
    
    # Get queue processor
    queue_processor = get_queue_processor()
    
    # Check if there's a currently executing job
    executing_job = queue_processor.get_executing_job(pump.id)
    stopped_job_name = None
    if executing_job:
        stopped_job_name = executing_job.zone_name
    
    # Clear the queue
    cleared_count = queue_processor.clear_queue(pump.id)
    
    # Build response message
    if executing_job and cleared_count > 0:
        message = (
            f"Emergency stop activated for pump '{pump.name}'. "
            f"Currently executing job will complete, then pump will stop. "
            f"Cleared {cleared_count} queued job(s)."
        )
    elif executing_job:
        message = (
            f"Emergency stop activated for pump '{pump.name}'. "
            f"Currently executing job will complete, then pump will stop."
        )
    elif cleared_count > 0:
        message = (
            f"Emergency stop activated for pump '{pump.name}'. "
            f"Cleared {cleared_count} queued job(s)."
        )
    else:
        message = f"Pump '{pump.name}' is idle with no queued jobs."
    
    return ManualStopResponse(
        message=message,
        pump_id=pump.id,
        pump_name=pump.name,
        stopped_job=stopped_job_name,
        cleared_jobs=cleared_count
    )
