"""
Event scheduler for v2 room-based irrigation system.

This module provides:
- Background scheduler that runs every 60 seconds
- P1 event calculation (lights-on + delay)
- P2 event calculation (specific time of day)
- Job creation and queue integration
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.models.database import SessionLocal
from backend.models.v2_room import Room
from backend.models.v2_water_event import WaterEvent
from backend.models.v2_zone import ZoneV2
from backend.services.ha_client import HomeAssistantClient, get_ha_client
from backend.services.queue_processor import ExecutionJob, get_queue_processor

logger = logging.getLogger(__name__)


class EventScheduler:
    """
    Scheduler that evaluates water events and creates execution jobs.
    
    The scheduler runs every 60 seconds and:
    1. Loads all enabled rooms and their events
    2. Calculates when each event should run
    3. Creates execution jobs for events that match the current time
    4. Adds jobs to the appropriate pump queues
    """
    
    def __init__(self, ha_client: Optional[HomeAssistantClient] = None):
        """
        Initialize the event scheduler.
        
        Args:
            ha_client: Optional HomeAssistantClient instance (uses singleton if not provided)
        """
        self.ha_client = ha_client or get_ha_client()
        self.queue_processor = get_queue_processor()
        
        # Background task handle
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("EventScheduler initialized")
    
    async def start(self) -> None:
        """
        Start the background scheduler task.
        
        The scheduler will run every 60 seconds until stopped.
        """
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Event scheduler started")
    
    async def stop(self) -> None:
        """
        Stop the background scheduler task.
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
        
        logger.info("Event scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """
        Main scheduler loop that runs every 60 seconds.
        
        Evaluates all events and creates jobs for those that should run now.
        """
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                await self._evaluate_events()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            
            # Wait 60 seconds before next iteration
            await asyncio.sleep(60)
        
        logger.info("Scheduler loop stopped")

    async def _evaluate_events(self) -> None:
        """
        Evaluate all enabled events and create jobs for those that should run now.
        
        This method:
        1. Loads all enabled rooms from the database
        2. For each room, loads all enabled water events
        3. Calculates when each event should run
        4. Creates execution jobs for events matching current time (within 60s window)
        5. Adds jobs to pump queues
        """
        current_time = datetime.now()
        logger.info(f"[SCHEDULER] Evaluating events at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get database session
        db = SessionLocal()
        try:
            # Load all enabled rooms
            rooms = db.query(Room).filter(Room.enabled == True).all()
            logger.debug(f"Found {len(rooms)} enabled rooms")
            
            if not rooms:
                logger.debug("No enabled rooms found, skipping evaluation")
                return
            
            # Process each room
            for room in rooms:
                try:
                    await self._evaluate_room_events(db, room, current_time)
                except Exception as e:
                    logger.error(
                        f"Error evaluating events for room {room.id} ({room.name}): {e}",
                        exc_info=True
                    )
        
        except Exception as e:
            logger.error(f"Error loading rooms from database: {e}", exc_info=True)
        
        finally:
            db.close()
    
    async def _evaluate_room_events(self, db: Session, room: Room, current_time: datetime) -> None:
        """
        Evaluate all events for a specific room.
        
        Args:
            db: Database session
            room: Room model instance
            current_time: Current datetime for comparison
        """
        logger.debug(f"Evaluating events for room {room.id} ({room.name})")
        
        # Load all enabled water events for this room
        events = db.query(WaterEvent).filter(
            WaterEvent.room_id == room.id,
            WaterEvent.enabled == True
        ).all()
        
        if not events:
            logger.debug(f"No enabled events for room {room.id}")
            return
        
        logger.debug(f"Found {len(events)} enabled events for room {room.id}")
        
        # Process each event
        for event in events:
            try:
                # Calculate when this event should run
                should_run, scheduled_time = await self._should_event_run(
                    room, event, current_time
                )
                
                if should_run:
                    logger.info(
                        f"Event {event.id} ({event.name}) should run now. "
                        f"Scheduled: {scheduled_time.strftime('%H:%M:%S')}"
                    )
                    await self._create_jobs_for_event(db, event, scheduled_time)
                else:
                    logger.debug(
                        f"Event {event.id} ({event.name}) not due. "
                        f"Next run: {scheduled_time.strftime('%H:%M:%S') if scheduled_time else 'N/A'}"
                    )
            
            except Exception as e:
                logger.error(
                    f"Error evaluating event {event.id} ({event.name}): {e}",
                    exc_info=True
                )

    async def _should_event_run(
        self, room: Room, event: WaterEvent, current_time: datetime
    ) -> tuple[bool, Optional[datetime]]:
        """
        Determine if an event should run at the current time.
        
        Args:
            room: Room model instance
            event: WaterEvent model instance
            current_time: Current datetime
        
        Returns:
            Tuple of (should_run, scheduled_time)
            - should_run: True if event should execute now
            - scheduled_time: When the event is scheduled (for logging)
        """
        if event.event_type == "p1":
            return await self._calculate_p1_event(room, event, current_time)
        elif event.event_type == "p2":
            return await self._calculate_p2_event(room, event, current_time)
        else:
            logger.error(f"Unknown event type '{event.event_type}' for event {event.id}")
            return False, None
    
    async def _calculate_p1_event(
        self, room: Room, event: WaterEvent, current_time: datetime
    ) -> tuple[bool, Optional[datetime]]:
        """
        Calculate if a P1 event should run.
        
        P1 events run at lights_on_time + delay_minutes.
        
        Args:
            room: Room model instance
            event: WaterEvent model instance (must be P1 type)
            current_time: Current datetime
        
        Returns:
            Tuple of (should_run, scheduled_time)
        """
        try:
            # Validate P1 event has required fields
            if event.delay_minutes is None:
                logger.error(f"P1 event {event.id} missing delay_minutes")
                return False, None
            
            # Get lights_on_entity value from Home Assistant
            if not room.lights_on_entity:
                logger.error(f"Room {room.id} missing lights_on_entity")
                return False, None
            
            try:
                lights_on_state = await self.ha_client.get_state(room.lights_on_entity)
                lights_on_value = lights_on_state.state
                logger.debug(f"Room {room.id} lights_on_entity value: {lights_on_value}")
            except Exception as e:
                logger.error(
                    f"Failed to get lights_on_entity '{room.lights_on_entity}' for room {room.id}: {e}"
                )
                return False, None
            
            # Parse lights_on time (format: HH:MM:SS or HH:MM)
            try:
                lights_on_time = datetime.strptime(lights_on_value, "%H:%M:%S").time()
            except ValueError:
                try:
                    lights_on_time = datetime.strptime(lights_on_value, "%H:%M").time()
                except ValueError:
                    logger.error(
                        f"Invalid lights_on time format '{lights_on_value}' for room {room.id}"
                    )
                    return False, None
            
            # Calculate scheduled time: lights_on + delay_minutes
            scheduled_datetime = datetime.combine(current_time.date(), lights_on_time)
            scheduled_datetime += timedelta(minutes=event.delay_minutes)
            
            # Check if current time matches (within 60s window)
            time_diff = abs((current_time - scheduled_datetime).total_seconds())
            should_run = time_diff < 60
            
            logger.debug(
                f"P1 event {event.id}: lights_on={lights_on_time}, "
                f"delay={event.delay_minutes}min, scheduled={scheduled_datetime.strftime('%H:%M:%S')}, "
                f"diff={time_diff:.0f}s, should_run={should_run}"
            )
            
            return should_run, scheduled_datetime
        
        except Exception as e:
            logger.error(f"Error calculating P1 event {event.id}: {e}", exc_info=True)
            return False, None
    
    async def _calculate_p2_event(
        self, room: Room, event: WaterEvent, current_time: datetime
    ) -> tuple[bool, Optional[datetime]]:
        """
        Calculate if a P2 event should run.
        
        P2 events run at a specific time_of_day (HH:MM format).
        
        Args:
            room: Room model instance
            event: WaterEvent model instance (must be P2 type)
            current_time: Current datetime
        
        Returns:
            Tuple of (should_run, scheduled_time)
        """
        try:
            # Validate P2 event has required fields
            if not event.time_of_day:
                logger.error(f"P2 event {event.id} missing time_of_day")
                return False, None
            
            # Parse time_of_day (format: HH:MM)
            try:
                scheduled_time = datetime.strptime(event.time_of_day, "%H:%M").time()
            except ValueError:
                logger.error(
                    f"Invalid time_of_day format '{event.time_of_day}' for event {event.id}"
                )
                return False, None
            
            # Create scheduled datetime for today
            scheduled_datetime = datetime.combine(current_time.date(), scheduled_time)
            
            # Check if current time matches (within 60s window)
            time_diff = abs((current_time - scheduled_datetime).total_seconds())
            should_run = time_diff < 60
            
            logger.debug(
                f"P2 event {event.id}: time_of_day={event.time_of_day}, "
                f"scheduled={scheduled_datetime.strftime('%H:%M:%S')}, "
                f"diff={time_diff:.0f}s, should_run={should_run}"
            )
            
            return should_run, scheduled_datetime
        
        except Exception as e:
            logger.error(f"Error calculating P2 event {event.id}: {e}", exc_info=True)
            return False, None

    async def _create_jobs_for_event(
        self, db: Session, event: WaterEvent, scheduled_time: datetime
    ) -> None:
        """
        Create execution jobs for all zones assigned to an event.
        
        For each zone assigned to the event:
        1. Create an ExecutionJob with zone details
        2. Add the job to the zone's pump queue
        
        Args:
            db: Database session
            event: WaterEvent model instance
            scheduled_time: When the event was scheduled to run
        """
        # Load zones for this event (with eager loading of pump relationship)
        zones = event.zones
        
        if not zones:
            logger.warning(f"Event {event.id} ({event.name}) has no zones assigned")
            return
        
        logger.info(
            f"Creating jobs for event {event.id} ({event.name}): "
            f"{len(zones)} zones, duration={event.run_time_seconds}s"
        )
        
        # Create a job for each zone
        for zone in zones:
            try:
                # Skip disabled zones
                if not zone.enabled:
                    logger.debug(f"Skipping disabled zone {zone.id} ({zone.name})")
                    continue
                
                # Get pump for this zone
                pump = zone.pump
                if not pump:
                    logger.error(f"Zone {zone.id} has no associated pump")
                    continue
                
                if not pump.enabled:
                    logger.debug(f"Skipping zone {zone.id} - pump {pump.id} is disabled")
                    continue
                
                # Create execution job
                job = ExecutionJob(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    switch_entity=zone.switch_entity,
                    duration_seconds=event.run_time_seconds,
                    scheduled_time=scheduled_time
                )
                
                # Add job to pump queue
                self.queue_processor.add_job(pump.id, job)
                
                logger.info(
                    f"Created job for zone {zone.id} ({zone.name}) on pump {pump.id} ({pump.name}): "
                    f"duration={event.run_time_seconds}s"
                )
            
            except Exception as e:
                logger.error(
                    f"Error creating job for zone {zone.id}: {e}",
                    exc_info=True
                )


# Singleton instance
_scheduler_instance: Optional[EventScheduler] = None


def get_scheduler() -> EventScheduler:
    """
    Get the singleton scheduler instance.
    
    Returns:
        EventScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = EventScheduler()
    return _scheduler_instance
