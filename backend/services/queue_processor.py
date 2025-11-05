"""
Pump Queue Processor Service

This module implements the queue processor that executes irrigation jobs
from pump queues. It runs every 1 second, checks pump lock status, and
executes jobs in FIFO order while respecting pump locks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from queue import Queue, Empty

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from ..models.database import SessionLocal
from ..models.pump import Pump
from .ha_client import HomeAssistantClient, HomeAssistantAPIError
from .scheduler import ExecutionJob


logger = logging.getLogger(__name__)


class QueueProcessor:
    """
    Queue processor that executes irrigation jobs from pump queues.
    
    The processor runs every 1 second, checks each pump's lock status,
    and executes jobs from the queue when the pump is idle. It implements
    safety mechanisms including pump locking and timeout handling.
    """
    
    def __init__(self, ha_client: HomeAssistantClient, pump_queues: Dict[int, Queue]):
        """
        Initialize the queue processor.
        
        Args:
            ha_client: Home Assistant API client for controlling switches and locks
            pump_queues: Dictionary mapping pump_id to Queue for job execution
        """
        self.ha_client = ha_client
        self.pump_queues = pump_queues
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Track active jobs and lock times for timeout detection
        self.active_jobs: Dict[int, ExecutionJob] = {}  # pump_id -> ExecutionJob
        self.lock_start_times: Dict[int, datetime] = {}  # pump_id -> lock start time
        
        # Timeout configuration (5 minutes)
        self.lock_timeout_seconds = 300
        
        # Status cache for performance (1-second cache)
        self._status_cache: Dict[int, Dict[str, Any]] = {}  # pump_id -> status dict
        self._status_cache_time: Dict[int, datetime] = {}  # pump_id -> cache timestamp
        self._cache_ttl_seconds = 1  # 1-second cache TTL
        
        logger.info("Queue processor initialized")
    
    def start(self):
        """Start the queue processor."""
        if self.is_running:
            logger.warning("Queue processor is already running")
            return
        
        # Add the processor tick job with 1-second interval
        self.scheduler.add_job(
            self.processor_tick,
            trigger=IntervalTrigger(seconds=1),
            id='processor_tick',
            name='Queue Processor Tick',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Queue processor started")
    
    def stop(self):
        """Stop the queue processor."""
        if not self.is_running:
            logger.warning("Queue processor is not running")
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Queue processor stopped")
    
    async def processor_tick(self):
        """
        Main processor tick function that runs every 1 second.
        
        This function:
        1. Loads all pumps from the database
        2. Checks each pump's lock status via Home Assistant
        3. Executes jobs from the queue when pump is idle
        4. Handles timeout for stuck locks
        """
        logger.debug("Processor tick started")
        
        try:
            # Get database session
            db = SessionLocal()
            
            try:
                # Load all pumps from database
                pumps = db.query(Pump).all()
                
                if not pumps:
                    logger.debug("No pumps found, skipping tick")
                    return
                
                # Process each pump
                for pump in pumps:
                    try:
                        await self._process_pump(pump)
                    except Exception as e:
                        logger.error(f"Error processing pump {pump.id} ({pump.name}): {str(e)}")
                        # Continue processing other pumps
                        continue
                
                logger.debug("Processor tick completed")
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error in processor tick: {str(e)}", exc_info=True)

    async def _process_pump(self, pump: Pump):
        """
        Process a single pump's queue.
        
        Checks the pump's lock status and executes the next job if the pump
        is idle and the queue is not empty.
        
        Args:
            pump: Pump object to process
        """
        pump_id = pump.id
        
        # Get or create queue for this pump
        if pump_id not in self.pump_queues:
            self.pump_queues[pump_id] = Queue()
            logger.debug(f"Created new queue for pump {pump_id}")
        
        queue = self.pump_queues[pump_id]
        
        # Check if pump has an active job
        if pump_id in self.active_jobs:
            # Check for timeout
            await self._check_lock_timeout(pump)
            return
        
        # Check if queue is empty
        if queue.empty():
            logger.debug(f"Queue for pump {pump_id} ({pump.name}) is empty")
            return
        
        # Check pump lock status
        try:
            lock_state = await self.ha_client.get_state(pump.lock_entity)
            is_locked = lock_state.state.lower() in ['on', 'true', 'locked']
            
            if is_locked:
                logger.debug(f"Pump {pump_id} ({pump.name}) is locked, waiting")
                return
            
            # Pump is idle and queue has jobs - execute next job
            try:
                job = queue.get_nowait()
                await self._execute_job(pump, job)
            except Empty:
                # Queue became empty between check and get
                logger.debug(f"Queue for pump {pump_id} became empty")
                return
        
        except HomeAssistantAPIError as e:
            logger.error(f"Failed to check lock status for pump {pump_id}: {str(e)}")
            return
    
    async def _check_lock_timeout(self, pump: Pump):
        """
        Check if a pump lock has timed out and force unlock if necessary.
        
        If a pump has been locked for more than the timeout period (5 minutes),
        this function will force unlock the pump and clear the active job.
        
        Args:
            pump: Pump object to check
        """
        pump_id = pump.id
        
        if pump_id not in self.lock_start_times:
            return
        
        lock_start = self.lock_start_times[pump_id]
        elapsed = (datetime.now() - lock_start).total_seconds()
        
        if elapsed > self.lock_timeout_seconds:
            logger.warning(
                f"Pump {pump_id} ({pump.name}) lock timeout after {elapsed:.1f}s, "
                f"forcing unlock"
            )
            
            # Force unlock the pump
            try:
                await self.ha_client.turn_off(pump.lock_entity)
                logger.info(f"Forced unlock of pump {pump_id} ({pump.name})")
            except HomeAssistantAPIError as e:
                logger.error(f"Failed to force unlock pump {pump_id}: {str(e)}")
            
            # Clear active job and lock time
            if pump_id in self.active_jobs:
                job = self.active_jobs[pump_id]
                logger.warning(
                    f"Clearing timed-out job for zone {job.zone_id} ({job.zone_name}) "
                    f"on pump {pump_id}"
                )
                del self.active_jobs[pump_id]
            
            if pump_id in self.lock_start_times:
                del self.lock_start_times[pump_id]

    async def _execute_job(self, pump: Pump, job: ExecutionJob):
        """
        Execute an irrigation job.
        
        This function implements the complete job execution sequence:
        1. Lock the pump
        2. Turn on the zone switch
        3. Wait for the specified duration
        4. Turn off the zone switch
        5. Unlock the pump
        
        Error handling ensures that switches are turned off and pumps are
        unlocked even if failures occur during execution.
        
        Args:
            pump: Pump object that controls this zone
            job: ExecutionJob to execute
        """
        pump_id = pump.id
        
        logger.info(
            f"Starting job execution: zone {job.zone_id} ({job.zone_name}) "
            f"on pump {pump_id} ({pump.name}), duration={job.duration_seconds}s"
        )
        
        # Mark job as active
        self.active_jobs[pump_id] = job
        self.lock_start_times[pump_id] = datetime.now()
        
        switch_turned_on = False
        
        try:
            # Step 1: Lock the pump
            try:
                await self.ha_client.turn_on(pump.lock_entity)
                logger.debug(f"Locked pump {pump_id} ({pump.name})")
            except HomeAssistantAPIError as e:
                logger.error(f"Failed to lock pump {pump_id}: {str(e)}")
                raise
            
            # Step 2: Turn on the zone switch
            try:
                await self.ha_client.turn_on(job.switch_entity)
                switch_turned_on = True
                logger.info(
                    f"Turned on switch {job.switch_entity} for zone {job.zone_id} "
                    f"({job.zone_name})"
                )
            except HomeAssistantAPIError as e:
                logger.error(
                    f"Failed to turn on switch {job.switch_entity} for zone "
                    f"{job.zone_id}: {str(e)}"
                )
                raise
            
            # Step 3: Wait for the specified duration
            logger.debug(f"Waiting {job.duration_seconds}s for zone {job.zone_id}")
            await asyncio.sleep(job.duration_seconds)
            
            # Step 4: Turn off the zone switch
            try:
                await self.ha_client.turn_off(job.switch_entity)
                logger.info(
                    f"Turned off switch {job.switch_entity} for zone {job.zone_id} "
                    f"({job.zone_name})"
                )
            except HomeAssistantAPIError as e:
                logger.error(
                    f"Failed to turn off switch {job.switch_entity} for zone "
                    f"{job.zone_id}: {str(e)}"
                )
                # Continue to unlock pump even if switch turn-off fails
            
            # Step 5: Unlock the pump
            try:
                await self.ha_client.turn_off(pump.lock_entity)
                logger.debug(f"Unlocked pump {pump_id} ({pump.name})")
            except HomeAssistantAPIError as e:
                logger.error(f"Failed to unlock pump {pump_id}: {str(e)}")
                # Log but don't raise - timeout mechanism will handle stuck locks
            
            logger.info(
                f"Completed job execution: zone {job.zone_id} ({job.zone_name}) "
                f"on pump {pump_id} ({pump.name})"
            )
        
        except Exception as e:
            # Error occurred during execution - attempt cleanup
            logger.error(
                f"Error executing job for zone {job.zone_id} ({job.zone_name}): {str(e)}",
                exc_info=True
            )
            
            # Attempt to turn off switch if it was turned on
            if switch_turned_on:
                try:
                    await self.ha_client.turn_off(job.switch_entity)
                    logger.info(f"Emergency turn-off of switch {job.switch_entity}")
                except Exception as cleanup_error:
                    logger.error(
                        f"Failed to turn off switch during error cleanup: {str(cleanup_error)}"
                    )
            
            # Attempt to unlock pump
            try:
                await self.ha_client.turn_off(pump.lock_entity)
                logger.info(f"Emergency unlock of pump {pump_id}")
            except Exception as cleanup_error:
                logger.error(
                    f"Failed to unlock pump during error cleanup: {str(cleanup_error)}"
                )
        
        finally:
            # Clear active job and lock time
            if pump_id in self.active_jobs:
                del self.active_jobs[pump_id]
            if pump_id in self.lock_start_times:
                del self.lock_start_times[pump_id]
            
            logger.debug(f"Cleared active job for pump {pump_id}")
    
    def get_pump_status(self, pump_id: int) -> Dict[str, Any]:
        """
        Get the current status of a pump with 1-second caching.
        
        Returns information about whether the pump is idle, running a zone,
        or has jobs queued. Results are cached for 1 second to improve
        performance when multiple requests are made in quick succession.
        
        Args:
            pump_id: ID of the pump to check
        
        Returns:
            Dictionary with status information:
            - status: 'idle', 'running', or 'queued'
            - active_zone: Name of active zone if running, None otherwise
            - queue_length: Number of jobs in queue
        """
        # Check if we have a valid cached status
        now = datetime.now()
        if pump_id in self._status_cache and pump_id in self._status_cache_time:
            cache_age = (now - self._status_cache_time[pump_id]).total_seconds()
            if cache_age < self._cache_ttl_seconds:
                logger.debug(f"Returning cached status for pump {pump_id} (age: {cache_age:.2f}s)")
                return self._status_cache[pump_id]
        
        # Calculate fresh status
        status = {
            'status': 'idle',
            'active_zone': None,
            'queue_length': 0
        }
        
        # Check if pump has an active job
        if pump_id in self.active_jobs:
            job = self.active_jobs[pump_id]
            status['status'] = 'running'
            status['active_zone'] = job.zone_name
        
        # Check queue length
        if pump_id in self.pump_queues:
            queue = self.pump_queues[pump_id]
            queue_length = queue.qsize()
            status['queue_length'] = queue_length
            
            # If not running but has queued jobs, status is 'queued'
            if status['status'] == 'idle' and queue_length > 0:
                status['status'] = 'queued'
        
        # Cache the status
        self._status_cache[pump_id] = status
        self._status_cache_time[pump_id] = now
        
        logger.debug(f"Calculated fresh status for pump {pump_id}: {status['status']}")
        return status
