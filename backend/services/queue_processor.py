"""
Pump queue processor for v2 room-based irrigation system.

This module provides:
- In-memory queue management per pump
- Job execution logic with pump lock coordination
- Background processing task that runs every 1 second
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from backend.services.ha_client import HomeAssistantClient, get_ha_client
from backend.models.database import SessionLocal
from backend.models.v2_pump import PumpV2
from backend.models.v2_settings import SystemSettings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionJob:
    """
    Represents a job to execute a zone irrigation.
    
    Attributes:
        zone_id: Database ID of the zone
        zone_name: Name of the zone (for logging)
        switch_entity: HA switch entity to control
        duration_seconds: How long to run the zone
        scheduled_time: When this job was scheduled
        created_at: When this job was created
    """
    zone_id: int
    zone_name: str
    switch_entity: str
    duration_seconds: int
    scheduled_time: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __repr__(self):
        return f"<ExecutionJob(zone='{self.zone_name}', duration={self.duration_seconds}s)>"


class PumpQueueProcessor:
    """
    Manages and processes execution queues for all pumps.
    
    Each pump has its own FIFO queue. The processor checks all queues
    every second and executes jobs when pumps are idle.
    """
    
    def __init__(self, ha_client: Optional[HomeAssistantClient] = None):
        """
        Initialize the queue processor.
        
        Args:
            ha_client: Optional HomeAssistantClient instance (uses singleton if not provided)
        """
        self.ha_client = ha_client or get_ha_client()
        
        # In-memory queues: pump_id -> List[ExecutionJob]
        self.queues: Dict[int, List[ExecutionJob]] = defaultdict(list)
        
        # Track currently executing jobs: pump_id -> ExecutionJob
        self.executing: Dict[int, Optional[ExecutionJob]] = {}
        
        # Background task handle
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("PumpQueueProcessor initialized")
    
    def add_job(self, pump_id: int, job: ExecutionJob) -> None:
        """
        Add a job to a pump's queue.
        
        Args:
            pump_id: Database ID of the pump
            job: ExecutionJob to add to the queue
        """
        try:
            self.queues[pump_id].append(job)
            queue_length = len(self.queues[pump_id])
            logger.info(
                f"Added job to pump {pump_id} queue: {job}. "
                f"Queue length: {queue_length}"
            )
        except Exception as e:
            logger.error(f"Failed to add job to pump {pump_id} queue: {e}", exc_info=True)
    
    def get_queue_length(self, pump_id: int) -> int:
        """
        Get the number of jobs in a pump's queue.
        
        Args:
            pump_id: Database ID of the pump
        
        Returns:
            Number of jobs in the queue
        """
        return len(self.queues.get(pump_id, []))
    
    def get_executing_job(self, pump_id: int) -> Optional[ExecutionJob]:
        """
        Get the currently executing job for a pump.
        
        Args:
            pump_id: Database ID of the pump
        
        Returns:
            ExecutionJob if pump is executing, None if idle
        """
        return self.executing.get(pump_id)
    
    def clear_queue(self, pump_id: int) -> int:
        """
        Clear all jobs from a pump's queue.
        
        Args:
            pump_id: Database ID of the pump
        
        Returns:
            Number of jobs that were cleared
        """
        count = len(self.queues.get(pump_id, []))
        self.queues[pump_id] = []
        logger.info(f"Cleared {count} jobs from pump {pump_id} queue")
        return count
    
    async def start(self) -> None:
        """
        Start the background queue processor task.
        
        The processor will run every 1 second until stopped.
        """
        if self._running:
            logger.warning("Queue processor already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Queue processor started")
    
    async def stop(self) -> None:
        """
        Stop the background queue processor task.
        """
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Queue processor stopped")
    
    async def _process_loop(self) -> None:
        """
        Main processing loop that runs every 1 second.
        
        Checks all pump queues and executes jobs when pumps are idle.
        """
        logger.info("Queue processor loop started")
        
        while self._running:
            try:
                await self._process_all_queues()
            except Exception as e:
                logger.error(f"Error in queue processor loop: {e}", exc_info=True)
            
            # Wait 1 second before next iteration
            await asyncio.sleep(1)
        
        logger.info("Queue processor loop stopped")
    
    async def _process_all_queues(self) -> None:
        """
        Process all pump queues once.
        
        For each pump with a non-empty queue, check if it's idle
        and execute the first job if so.
        """
        # Get all pumps from database
        db = SessionLocal()
        try:
            pumps = db.query(PumpV2).filter(PumpV2.enabled == True).all()
            logger.debug(f"Processing queues for {len(pumps)} enabled pumps")
            
            for pump in pumps:
                try:
                    # Skip if no jobs in queue
                    if pump.id not in self.queues or not self.queues[pump.id]:
                        continue
                    
                    queue_length = len(self.queues[pump.id])
                    logger.debug(f"Pump {pump.id} ({pump.name}) has {queue_length} jobs in queue")
                    
                    # Skip if pump is currently executing a job
                    if pump.id in self.executing and self.executing[pump.id] is not None:
                        logger.debug(f"Pump {pump.id} is currently executing a job, skipping")
                        continue
                    
                    # Check if pump lock is idle
                    try:
                        is_idle = await self.ha_client.is_entity_off(pump.lock_entity)
                        logger.debug(f"Pump {pump.id} lock state: {'idle' if is_idle else 'busy'}")
                        
                        if is_idle:
                            # Execute first job in queue
                            job = self.queues[pump.id].pop(0)
                            logger.info(
                                f"Starting job execution for pump {pump.id} ({pump.name}): "
                                f"zone='{job.zone_name}', duration={job.duration_seconds}s, "
                                f"remaining_queue={len(self.queues[pump.id])}"
                            )
                            
                            # Mark as executing
                            self.executing[pump.id] = job
                            
                            # Execute job in background (don't await)
                            asyncio.create_task(self._execute_job(pump, job))
                        else:
                            logger.debug(f"Pump {pump.id} is busy, waiting for it to become idle")
                    
                    except ValueError as e:
                        # Entity not found
                        logger.error(
                            f"Pump {pump.id} lock entity '{pump.lock_entity}' not found in HA: {e}. "
                            f"Skipping pump."
                        )
                    except Exception as e:
                        logger.error(
                            f"Error checking pump {pump.id} lock state: {e}. "
                            f"Will retry on next cycle.",
                            exc_info=True
                        )
                
                except Exception as e:
                    logger.error(
                        f"Error processing pump {pump.id}: {e}. "
                        f"Continuing with next pump.",
                        exc_info=True
                    )
        
        except Exception as e:
            logger.error(f"Error loading pumps from database: {e}", exc_info=True)
        
        finally:
            db.close()
    
    async def _execute_job(self, pump: PumpV2, job: ExecutionJob) -> None:
        """
        Execute a single irrigation job.
        
        Execution sequence:
        1. Turn on pump lock
        2. Wait for pump startup delay (from settings)
        3. Turn on zone switch
        4. Wait for job duration
        5. Turn off zone switch
        6. Wait for zone switch delay (from settings)
        7. Turn off pump lock
        8. Mark job as complete
        
        Args:
            pump: PumpV2 model instance
            job: ExecutionJob to execute
        """
        start_time = datetime.utcnow()
        logger.info(
            f"[EXECUTION START] Pump: {pump.id} ({pump.name}), "
            f"Zone: {job.zone_name} (ID: {job.zone_id}), "
            f"Duration: {job.duration_seconds}s, "
            f"Scheduled: {job.scheduled_time}"
        )
        
        # Get system settings for delays
        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
            if not settings:
                logger.error("System settings not found, using default delays")
                pump_startup_delay = 5
                zone_switch_delay = 2
            else:
                pump_startup_delay = settings.pump_startup_delay_seconds
                zone_switch_delay = settings.zone_switch_delay_seconds
                logger.debug(
                    f"Using system settings: pump_delay={pump_startup_delay}s, "
                    f"zone_delay={zone_switch_delay}s"
                )
        except Exception as e:
            logger.error(f"Error loading system settings: {e}. Using defaults.", exc_info=True)
            pump_startup_delay = 5
            zone_switch_delay = 2
        finally:
            db.close()
        
        pump_lock_on = False
        zone_switch_on = False
        
        try:
            # Step 1: Turn on pump lock
            logger.info(f"[STEP 1/7] Turning on pump lock: {pump.lock_entity}")
            try:
                await self.ha_client.turn_on(pump.lock_entity)
                pump_lock_on = True
                logger.info(f"Pump lock activated: {pump.lock_entity}")
            except Exception as e:
                logger.error(f"Failed to turn on pump lock {pump.lock_entity}: {e}", exc_info=True)
                raise
            
            # Step 2: Wait for pump startup delay
            logger.info(f"[STEP 2/7] Waiting {pump_startup_delay}s for pump startup")
            await asyncio.sleep(pump_startup_delay)
            
            # Step 3: Turn on zone switch
            logger.info(f"[STEP 3/7] Turning on zone switch: {job.switch_entity}")
            try:
                await self.ha_client.turn_on(job.switch_entity)
                zone_switch_on = True
                logger.info(f"Zone switch activated: {job.switch_entity}")
            except Exception as e:
                logger.error(f"Failed to turn on zone switch {job.switch_entity}: {e}", exc_info=True)
                raise
            
            # Step 4: Wait for job duration
            logger.info(f"[STEP 4/7] Running zone '{job.zone_name}' for {job.duration_seconds}s")
            await asyncio.sleep(job.duration_seconds)
            
            # Step 5: Turn off zone switch
            logger.info(f"[STEP 5/7] Turning off zone switch: {job.switch_entity}")
            try:
                await self.ha_client.turn_off(job.switch_entity)
                zone_switch_on = False
                logger.info(f"Zone switch deactivated: {job.switch_entity}")
            except Exception as e:
                logger.error(f"Failed to turn off zone switch {job.switch_entity}: {e}", exc_info=True)
                # Continue to try turning off pump lock
            
            # Step 6: Wait for zone switch delay
            logger.info(f"[STEP 6/7] Waiting {zone_switch_delay}s for zone switch delay")
            await asyncio.sleep(zone_switch_delay)
            
            # Step 7: Turn off pump lock
            logger.info(f"[STEP 7/7] Turning off pump lock: {pump.lock_entity}")
            try:
                await self.ha_client.turn_off(pump.lock_entity)
                pump_lock_on = False
                logger.info(f"Pump lock deactivated: {pump.lock_entity}")
            except Exception as e:
                logger.error(f"Failed to turn off pump lock {pump.lock_entity}: {e}", exc_info=True)
                # Log but don't raise - job is essentially complete
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(
                f"[EXECUTION SUCCESS] Pump: {pump.id}, Zone: {job.zone_name}, "
                f"Total time: {duration:.1f}s"
            )
        
        except asyncio.CancelledError:
            logger.warning(
                f"[EXECUTION CANCELLED] Job cancelled for pump {pump.id}, zone {job.zone_name}"
            )
            # Perform cleanup
            await self._cleanup_after_error(
                pump, job, pump_lock_on, zone_switch_on, zone_switch_delay
            )
            raise
        
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.error(
                f"[EXECUTION FAILED] Pump: {pump.id}, Zone: {job.zone_name}, "
                f"Error: {e}, Time elapsed: {duration:.1f}s",
                exc_info=True
            )
            
            # Attempt cleanup
            await self._cleanup_after_error(
                pump, job, pump_lock_on, zone_switch_on, zone_switch_delay
            )
        
        finally:
            # Step 8: Mark job as complete (remove from executing)
            self.executing[pump.id] = None
            logger.info(f"Job execution finished for pump {pump.id}, zone {job.zone_name}")
    
    async def _cleanup_after_error(
        self,
        pump: PumpV2,
        job: ExecutionJob,
        pump_lock_on: bool,
        zone_switch_on: bool,
        zone_switch_delay: int
    ) -> None:
        """
        Cleanup after a job execution error.
        
        Attempts to turn off zone switch and pump lock to prevent
        equipment from being left in an active state.
        
        Args:
            pump: PumpV2 model instance
            job: ExecutionJob that failed
            pump_lock_on: Whether pump lock was turned on
            zone_switch_on: Whether zone switch was turned on
            zone_switch_delay: Delay to wait after turning off zone
        """
        logger.info(
            f"[CLEANUP] Starting cleanup for pump {pump.id}, zone {job.zone_name}. "
            f"pump_lock_on={pump_lock_on}, zone_switch_on={zone_switch_on}"
        )
        
        cleanup_errors = []
        
        # Turn off zone switch if it was turned on
        if zone_switch_on:
            try:
                logger.info(f"[CLEANUP] Turning off zone switch: {job.switch_entity}")
                await self.ha_client.turn_off(job.switch_entity)
                logger.info(f"[CLEANUP] Zone switch turned off successfully")
                await asyncio.sleep(zone_switch_delay)
            except Exception as e:
                error_msg = f"Failed to turn off zone switch {job.switch_entity}: {e}"
                logger.error(f"[CLEANUP] {error_msg}")
                cleanup_errors.append(error_msg)
        
        # Turn off pump lock if it was turned on
        if pump_lock_on:
            try:
                logger.info(f"[CLEANUP] Turning off pump lock: {pump.lock_entity}")
                await self.ha_client.turn_off(pump.lock_entity)
                logger.info(f"[CLEANUP] Pump lock turned off successfully")
            except Exception as e:
                error_msg = f"Failed to turn off pump lock {pump.lock_entity}: {e}"
                logger.error(f"[CLEANUP] {error_msg}")
                cleanup_errors.append(error_msg)
        
        if cleanup_errors:
            logger.error(
                f"[CLEANUP] Cleanup completed with {len(cleanup_errors)} error(s). "
                f"Manual intervention may be required."
            )
        else:
            logger.info(f"[CLEANUP] Cleanup completed successfully")


# Singleton instance
_queue_processor_instance: Optional[PumpQueueProcessor] = None


def get_queue_processor() -> PumpQueueProcessor:
    """
    Get the singleton queue processor instance.
    
    Returns:
        PumpQueueProcessor instance
    """
    global _queue_processor_instance
    if _queue_processor_instance is None:
        _queue_processor_instance = PumpQueueProcessor()
    return _queue_processor_instance
