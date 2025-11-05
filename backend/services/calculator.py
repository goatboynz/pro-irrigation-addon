"""
Schedule Calculator Service

This module provides functions for calculating irrigation schedules based on
zone configurations and global settings. It supports both auto mode (calculated
from light schedules) and manual mode (user-specified times).
"""

import logging
import re
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ScheduledEvent:
    """Represents a scheduled irrigation event"""
    time: datetime
    duration_seconds: int
    event_type: str  # 'P1' or 'P2'


@dataclass
class GlobalTimingSettings:
    """Container for global timing settings retrieved from Home Assistant"""
    lights_on_time: time
    lights_off_time: time
    p1_start_delay_minutes: int
    p2_start_delay_minutes: int
    p2_end_buffer_minutes: int


class ScheduleCalculationError(Exception):
    """Raised when schedule calculation fails"""
    pass


class ManualScheduleParseError(Exception):
    """Raised when manual schedule parsing fails"""
    pass


def calculate_auto_schedule(
    zone_config: Dict[str, Any],
    global_settings: GlobalTimingSettings,
    target_date: Optional[datetime] = None
) -> List[ScheduledEvent]:
    """
    Calculate automatic schedule for a zone based on global light timing settings.
    
    Implements the P1/P2 algorithm:
    - P1: Single event at lights_on + p1_start_delay
    - P2: Multiple events distributed between p2_start and p2_end
    
    Args:
        zone_config: Dictionary containing zone configuration with keys:
                    - p1_duration_sec: Duration of P1 event in seconds
                    - p2_event_count: Number of P2 events
                    - p2_duration_sec: Duration of each P2 event in seconds
        global_settings: GlobalTimingSettings object with timing parameters
        target_date: Optional date to calculate schedule for (defaults to today)
    
    Returns:
        List of ScheduledEvent objects sorted by time
        
    Raises:
        ScheduleCalculationError: If calculation fails due to invalid parameters
    """
    if target_date is None:
        target_date = datetime.now()
    
    events = []
    
    try:
        # Extract zone configuration
        p1_duration = zone_config.get('p1_duration_sec', 0)
        p2_event_count = zone_config.get('p2_event_count', 0)
        p2_duration = zone_config.get('p2_duration_sec', 0)
        
        # Calculate P1 event time
        # P1 = lights_on + p1_start_delay
        lights_on_dt = datetime.combine(target_date.date(), global_settings.lights_on_time)
        p1_start = lights_on_dt + timedelta(minutes=global_settings.p1_start_delay_minutes)
        
        if p1_duration > 0:
            events.append(ScheduledEvent(
                time=p1_start,
                duration_seconds=p1_duration,
                event_type='P1'
            ))
            logger.debug(f"Calculated P1 event at {p1_start} for {p1_duration}s")
        
        # Calculate P2 events
        if p2_event_count > 0 and p2_duration > 0:
            # P2 start = lights_on + p2_start_delay
            p2_start = lights_on_dt + timedelta(minutes=global_settings.p2_start_delay_minutes)
            
            # P2 end = lights_off - p2_end_buffer
            lights_off_dt = datetime.combine(target_date.date(), global_settings.lights_off_time)
            
            # Handle case where lights_off is on the next day
            if global_settings.lights_off_time < global_settings.lights_on_time:
                lights_off_dt += timedelta(days=1)
            
            p2_end = lights_off_dt - timedelta(minutes=global_settings.p2_end_buffer_minutes)
            
            # Calculate P2 window duration
            p2_window = p2_end - p2_start
            
            if p2_window.total_seconds() <= 0:
                logger.warning(
                    f"Invalid P2 window: start={p2_start}, end={p2_end}. "
                    "P2 events will not be scheduled."
                )
            else:
                # Distribute events evenly across the window
                if p2_event_count == 1:
                    # Single event at the start of the window
                    spacing_seconds = 0
                else:
                    # Multiple events distributed evenly
                    spacing_seconds = p2_window.total_seconds() / p2_event_count
                
                for i in range(p2_event_count):
                    event_time = p2_start + timedelta(seconds=i * spacing_seconds)
                    events.append(ScheduledEvent(
                        time=event_time,
                        duration_seconds=p2_duration,
                        event_type='P2'
                    ))
                    logger.debug(f"Calculated P2 event {i+1}/{p2_event_count} at {event_time} for {p2_duration}s")
        
        # Sort events by time
        events.sort(key=lambda e: e.time)
        
        logger.info(f"Calculated {len(events)} auto schedule events")
        return events
    
    except Exception as e:
        logger.error(f"Error calculating auto schedule: {str(e)}")
        raise ScheduleCalculationError(f"Failed to calculate auto schedule: {str(e)}")


def parse_manual_schedule(
    schedule_text: Optional[str],
    event_type: str,
    target_date: Optional[datetime] = None
) -> List[ScheduledEvent]:
    """
    Parse manual schedule text in HH:MM.SS format.
    
    Format: Each line contains a time and duration in the format HH:MM.SS
    where HH:MM is the time of day and SS is the duration in seconds.
    
    Examples:
        "08:30.120" - Event at 8:30 AM for 120 seconds
        "14:15.90"  - Event at 2:15 PM for 90 seconds
    
    Args:
        schedule_text: Text containing schedule entries, one per line
        event_type: Type of events ('P1' or 'P2')
        target_date: Optional date to calculate schedule for (defaults to today)
    
    Returns:
        List of ScheduledEvent objects sorted by time
        
    Raises:
        ManualScheduleParseError: If parsing fails due to invalid format
    """
    if not schedule_text or not schedule_text.strip():
        return []
    
    if target_date is None:
        target_date = datetime.now()
    
    events = []
    
    # Pattern: HH:MM.SS where HH is hours (00-23), MM is minutes (00-59), SS is duration in seconds
    pattern = r'^(\d{1,2}):(\d{2})\.(\d+)$'
    
    lines = schedule_text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        match = re.match(pattern, line)
        
        if not match:
            error_msg = (
                f"Invalid manual schedule format on line {line_num}: '{line}'. "
                f"Expected format: HH:MM.SS (e.g., '08:30.120')"
            )
            logger.error(error_msg)
            raise ManualScheduleParseError(error_msg)
        
        try:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            duration_seconds = int(match.group(3))
            
            # Validate time components
            if hours < 0 or hours > 23:
                raise ValueError(f"Hours must be between 0 and 23, got {hours}")
            
            if minutes < 0 or minutes > 59:
                raise ValueError(f"Minutes must be between 0 and 59, got {minutes}")
            
            if duration_seconds <= 0:
                raise ValueError(f"Duration must be positive, got {duration_seconds}")
            
            # Create datetime for the event
            event_time = datetime.combine(
                target_date.date(),
                time(hour=hours, minute=minutes)
            )
            
            events.append(ScheduledEvent(
                time=event_time,
                duration_seconds=duration_seconds,
                event_type=event_type
            ))
            
            logger.debug(
                f"Parsed {event_type} event from line {line_num}: "
                f"{event_time} for {duration_seconds}s"
            )
        
        except ValueError as e:
            error_msg = f"Invalid values on line {line_num}: {str(e)}"
            logger.error(error_msg)
            raise ManualScheduleParseError(error_msg)
    
    # Sort events by time
    events.sort(key=lambda e: e.time)
    
    logger.info(f"Parsed {len(events)} manual {event_type} events")
    return events


def validate_manual_schedule_format(schedule_text: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate manual schedule format without parsing to datetime.
    
    Args:
        schedule_text: Text containing schedule entries to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
        If invalid, error_message contains the validation error
    """
    if not schedule_text or not schedule_text.strip():
        return True, None  # Empty schedule is valid
    
    pattern = r'^(\d{1,2}):(\d{2})\.(\d+)$'
    lines = schedule_text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        match = re.match(pattern, line)
        
        if not match:
            return False, (
                f"Invalid format on line {line_num}: '{line}'. "
                f"Expected format: HH:MM.SS (e.g., '08:30.120')"
            )
        
        try:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            duration_seconds = int(match.group(3))
            
            if hours < 0 or hours > 23:
                return False, f"Line {line_num}: Hours must be between 0 and 23, got {hours}"
            
            if minutes < 0 or minutes > 59:
                return False, f"Line {line_num}: Minutes must be between 0 and 59, got {minutes}"
            
            if duration_seconds <= 0:
                return False, f"Line {line_num}: Duration must be positive, got {duration_seconds}"
        
        except ValueError as e:
            return False, f"Line {line_num}: {str(e)}"
    
    return True, None


def get_next_run_time(
    zone: Any,
    global_settings: Optional[GlobalTimingSettings] = None,
    current_time: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculate the next scheduled run time for a zone.
    
    This function handles both auto and manual mode zones:
    - Auto mode: Calculates schedule using global settings
    - Manual mode: Parses manual schedule entries
    
    Args:
        zone: Zone object with configuration (mode, schedule parameters)
        global_settings: GlobalTimingSettings object (required for auto mode)
        current_time: Optional current time (defaults to now)
    
    Returns:
        datetime of next scheduled event, or None if no upcoming events
        
    Raises:
        ScheduleCalculationError: If calculation fails
        ManualScheduleParseError: If manual schedule parsing fails
    """
    if current_time is None:
        current_time = datetime.now()
    
    try:
        events = []
        
        if zone.mode == 'auto':
            # Auto mode requires global settings
            if global_settings is None:
                logger.warning(f"Cannot calculate next run for zone {zone.id}: global settings not provided")
                return None
            
            # Build zone config dictionary
            zone_config = {
                'p1_duration_sec': zone.p1_duration_sec or 0,
                'p2_event_count': zone.p2_event_count or 0,
                'p2_duration_sec': zone.p2_duration_sec or 0
            }
            
            # Calculate schedule for today
            events = calculate_auto_schedule(zone_config, global_settings, current_time)
            
            # If no future events today, try tomorrow
            future_events = [e for e in events if e.time > current_time]
            if not future_events:
                tomorrow = current_time + timedelta(days=1)
                events = calculate_auto_schedule(zone_config, global_settings, tomorrow)
                future_events = [e for e in events if e.time > current_time]
        
        elif zone.mode == 'manual':
            # Parse P1 and P2 manual schedules
            p1_events = parse_manual_schedule(zone.p1_manual_list, 'P1', current_time)
            p2_events = parse_manual_schedule(zone.p2_manual_list, 'P2', current_time)
            
            events = p1_events + p2_events
            events.sort(key=lambda e: e.time)
            
            # Filter for future events today
            future_events = [e for e in events if e.time > current_time]
            
            # If no future events today, try tomorrow
            if not future_events:
                tomorrow = current_time + timedelta(days=1)
                p1_events = parse_manual_schedule(zone.p1_manual_list, 'P1', tomorrow)
                p2_events = parse_manual_schedule(zone.p2_manual_list, 'P2', tomorrow)
                events = p1_events + p2_events
                events.sort(key=lambda e: e.time)
                future_events = [e for e in events if e.time > current_time]
        
        else:
            logger.warning(f"Unknown zone mode '{zone.mode}' for zone {zone.id}")
            return None
        
        # Return the next event time
        if future_events:
            next_event = future_events[0]
            logger.debug(f"Next run for zone {zone.id} ({zone.name}): {next_event.time}")
            return next_event.time
        else:
            logger.debug(f"No upcoming events for zone {zone.id} ({zone.name})")
            return None
    
    except (ScheduleCalculationError, ManualScheduleParseError) as e:
        logger.error(f"Error calculating next run time for zone {zone.id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating next run time for zone {zone.id}: {str(e)}")
        raise ScheduleCalculationError(f"Failed to calculate next run time: {str(e)}")
