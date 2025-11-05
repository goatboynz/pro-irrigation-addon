"""
Scheduler Engine Service

This module implements the scheduler engine that evaluates zone schedules
every 60 seconds and creates execution jobs for zones that are due to run.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from queue import Queue
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from ..models.database import SessionLocal
from ..models.zone import Zone
from ..models.global_settings import GlobalSettings
from .ha_client import HomeAssistantClient
from .calculator import (
    GlobalTimingSettings,
    calculate_auto_schedule,
    parse_manual_schedule,
    ScheduleCalculationError,
    ManualScheduleParseError
)


logger = logging.getLogger(__name__)


@dataclass
class ExecutionJob:
    """
    Represents an execution job for a zone.
    
    This data structure is added to pump queues and contains all information
    needed to execute an irrigation event.
    """
    zone_id: int
    zone_name: str
    switch_entity: str
    duration_seconds: int
    scheduled_time: datetime
    created_at: datetime


class SchedulerEngine:
    """
    Scheduler engine that evaluates zone schedules and creates execution jobs.
    
    The scheduler runs every 60 seconds, loads all enabled zones, retrieves
    global settings from Home Assistant, calculates scheduled times, and
    creates execution jobs for zones that are due to run.
    """
    
    def __init__(self, ha_client: HomeAssistantClient, pump_queues: Dict[int, Queue]):
        """
        Initialize the scheduler engine.
        
        Args:
            ha_client: Home Assistant API client for retrieving global settings
            pump_queues: Dictionary mapping pump_id to Queue for job execution
        """
        self.ha_client = ha_client
        self.pump_queues = pump_queues
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        logger.info("Scheduler engine initialized")
    
    def start(self):
        """Start the scheduler engine."""
        if self.is_running:
            logger.warning("Scheduler engine is already running")
            return
        
        # Add the scheduler tick job with 60-second interval
        self.scheduler.add_job(
            self.scheduler_tick,
            trigger=IntervalTrigger(seconds=60),
            id='scheduler_tick',
            name='Scheduler Tick',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler engine started")
    
    def stop(self):
        """Stop the scheduler engine."""
        if not self.is_running:
            logger.warning("Scheduler engine is not running")
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Scheduler engine stopped")
    
    async def scheduler_tick(self):
        """
        Main scheduler tick function that runs every 60 seconds.
        
        This function:
        1. Loads all enabled zones from the database
        2. Retrieves global settings from Home Assistant
        3. Calculates scheduled times for each zone
        4. Creates execution jobs for zones that are due to run
        """
        logger.debug("Scheduler tick started")
        
        try:
            # Get database session
            db = SessionLocal()
            
            try:
                # Load all enabled zones from database
                zones = db.query(Zone).filter(Zone.enabled == True).all()
                logger.debug(f"Loaded {len(zones)} enabled zones")
                
                if not zones:
                    logger.debug("No enabled zones found, skipping tick")
                    return
                
                # Retrieve global settings from Home Assistant
                global_settings = await self._load_global_settings(db)
                
                if global_settings is None:
                    logger.warning("Could not load global settings, skipping tick")
                    return
                
                # Get current time for matching
                current_time = datetime.now()
                
                # Process each zone
                for zone in zones:
                    try:
                        await self._process_zone(zone, global_settings, current_time)
                    except Exception as e:
                        logger.error(f"Error processing zone {zone.id} ({zone.name}): {str(e)}")
                        # Continue processing other zones
                        continue
                
                logger.debug("Scheduler tick completed")
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error in scheduler tick: {str(e)}", exc_info=True)
    
    async def _load_global_settings(self, db: Session) -> Optional[GlobalTimingSettings]:
        """
        Load global settings from database and retrieve values from Home Assistant.
        
        Args:
            db: Database session
        
        Returns:
            GlobalTimingSettings object or None if settings cannot be loaded
        """
        try:
            # Get global settings from database
            settings = db.query(GlobalSettings).first()
            
            if not settings:
                logger.warning("No global settings found in database")
                return None
            
            # Check if all required entities are configured
            if not all([
                settings.lights_on_entity,
                settings.lights_off_entity,
                settings.p1_delay_entity,
                settings.p2_delay_entity,
                settings.p2_buffer_entity
            ]):
                logger.warning("Global settings are incomplete, some entities not configured")
                return None
            
            # Retrieve entity states from Home Assistant
            lights_on_state = await self.ha_client.get_state(settings.lights_on_entity)
            lights_off_state = await self.ha_client.get_state(settings.lights_off_entity)
            p1_delay_state = await self.ha_client.get_state(settings.p1_delay_entity)
            p2_delay_state = await self.ha_client.get_state(settings.p2_delay_entity)
            p2_buffer_state = await self.ha_client.get_state(settings.p2_buffer_entity)
            
            # Parse time values from input_datetime entities
            # Format is typically "HH:MM:SS" or "HH:MM"
            lights_on_time = self._parse_time(lights_on_state.state)
            lights_off_time = self._parse_time(lights_off_state.state)
            
            # Parse numeric values from input_number entities
            p1_delay_minutes = int(float(p1_delay_state.state))
            p2_delay_minutes = int(float(p2_delay_state.state))
            p2_buffer_minutes = int(float(p2_buffer_state.state))
            
            global_timing = GlobalTimingSettings(
                lights_on_time=lights_on_time,
                lights_off_time=lights_off_time,
                p1_start_delay_minutes=p1_delay_minutes,
                p2_start_delay_minutes=p2_delay_minutes,
                p2_end_buffer_minutes=p2_buffer_minutes
            )
            
            logger.debug(
                f"Loaded global settings: lights_on={lights_on_time}, "
                f"lights_off={lights_off_time}, p1_delay={p1_delay_minutes}min, "
                f"p2_delay={p2_delay_minutes}min, p2_buffer={p2_buffer_minutes}min"
            )
            
            return global_timing
        
        except Exception as e:
            logger.error(f"Error loading global settings: {str(e)}")
            return None
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parse time string from Home Assistant input_datetime entity.
        
        Args:
            time_str: Time string in format "HH:MM:SS" or "HH:MM"
        
        Returns:
            time object
        
        Raises:
            ValueError: If time string cannot be parsed
        """
        try:
            # Try parsing with seconds
            if time_str.count(':') == 2:
                dt = datetime.strptime(time_str, "%H:%M:%S")
            else:
                dt = datetime.strptime(time_str, "%H:%M")
            
            return dt.time()
        
        except ValueError as e:
            logger.error(f"Failed to parse time string '{time_str}': {str(e)}")
            raise
    
    async def _process_zone(
        self,
        zone: Zone,
        global_settings: GlobalTimingSettings,
        current_time: datetime
    ):
        """
        Process a single zone to check if it should run now.
        
        Calculates scheduled times for the zone and creates execution jobs
        for events that match the current time (within 60-second window).
        
        Args:
            zone: Zone object to process
            global_settings: Global timing settings
            current_time: Current datetime for matching
        """
        try:
            # Calculate scheduled times based on zone mode
            scheduled_events = []
            
            if zone.mode == 'auto':
                # Build zone config for auto mode calculation
                zone_config = {
                    'p1_duration_sec': zone.p1_duration_sec or 0,
                    'p2_event_count': zone.p2_event_count or 0,
                    'p2_duration_sec': zone.p2_duration_sec or 0
                }
                
                scheduled_events = calculate_auto_schedule(
                    zone_config,
                    global_settings,
                    current_time
                )
            
            elif zone.mode == 'manual':
                # Parse manual schedules for P1 and P2
                p1_events = parse_manual_schedule(
                    zone.p1_manual_list,
                    'P1',
                    current_time
                )
                p2_events = parse_manual_schedule(
                    zone.p2_manual_list,
                    'P2',
                    current_time
                )
                
                scheduled_events = p1_events + p2_events
                scheduled_events.sort(key=lambda e: e.time)
            
            else:
                logger.warning(f"Unknown mode '{zone.mode}' for zone {zone.id} ({zone.name})")
                return
            
            # Check if any events match current time (within 60-second window)
            for event in scheduled_events:
                if self._is_time_match(event.time, current_time):
                    # Create execution job
                    job = ExecutionJob(
                        zone_id=zone.id,
                        zone_name=zone.name,
                        switch_entity=zone.switch_entity,
                        duration_seconds=event.duration_seconds,
                        scheduled_time=event.time,
                        created_at=current_time
                    )
                    
                    # Add job to appropriate pump queue
                    self._add_job_to_queue(zone.pump_id, job)
                    
                    logger.info(
                        f"Created execution job for zone {zone.id} ({zone.name}) "
                        f"on pump {zone.pump_id}, duration={event.duration_seconds}s"
                    )
        
        except (ScheduleCalculationError, ManualScheduleParseError) as e:
            logger.error(f"Error calculating schedule for zone {zone.id} ({zone.name}): {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error processing zone {zone.id} ({zone.name}): {str(e)}",
                exc_info=True
            )
    
    def _is_time_match(self, scheduled_time: datetime, current_time: datetime) -> bool:
        """
        Check if scheduled time matches current time within 60-second window.
        
        The scheduler runs every 60 seconds, so we need to match events that
        are scheduled within the current minute.
        
        Args:
            scheduled_time: The scheduled event time
            current_time: The current time
        
        Returns:
            True if times match within 60-second window, False otherwise
        """
        # Calculate time difference in seconds
        time_diff = abs((scheduled_time - current_time).total_seconds())
        
        # Match if within 60-second window (30 seconds before or after)
        # This accounts for scheduler timing variations
        is_match = time_diff <= 30
        
        if is_match:
            logger.debug(
                f"Time match: scheduled={scheduled_time}, current={current_time}, "
                f"diff={time_diff:.1f}s"
            )
        
        return is_match
    
    def _add_job_to_queue(self, pump_id: int, job: ExecutionJob):
        """
        Add an execution job to the appropriate pump queue.
        
        Args:
            pump_id: ID of the pump that controls this zone
            job: ExecutionJob to add to the queue
        """
        # Get or create queue for this pump
        if pump_id not in self.pump_queues:
            self.pump_queues[pump_id] = Queue()
            logger.info(f"Created new queue for pump {pump_id}")
        
        # Add job to queue
        queue = self.pump_queues[pump_id]
        queue.put(job)
        
        logger.debug(
            f"Added job to pump {pump_id} queue: zone={job.zone_name}, "
            f"duration={job.duration_seconds}s, queue_size={queue.qsize()}"
        )
