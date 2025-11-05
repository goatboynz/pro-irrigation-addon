"""
Unit tests for schedule calculator service.

Tests the core schedule calculation logic including:
- Auto mode P1/P2 algorithm
- Manual schedule parsing
- Next run time calculation
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, time, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from calculator module to avoid circular imports
import importlib.util
spec = importlib.util.spec_from_file_location("calculator", Path(__file__).parent.parent / "services" / "calculator.py")
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)

calculate_auto_schedule = calculator.calculate_auto_schedule
parse_manual_schedule = calculator.parse_manual_schedule
validate_manual_schedule_format = calculator.validate_manual_schedule_format
get_next_run_time = calculator.get_next_run_time
GlobalTimingSettings = calculator.GlobalTimingSettings
ScheduleCalculationError = calculator.ScheduleCalculationError
ManualScheduleParseError = calculator.ManualScheduleParseError


class MockZone:
    """Mock zone object for testing"""
    def __init__(self, zone_id, name, mode, **kwargs):
        self.id = zone_id
        self.name = name
        self.mode = mode
        self.p1_duration_sec = kwargs.get('p1_duration_sec')
        self.p2_event_count = kwargs.get('p2_event_count')
        self.p2_duration_sec = kwargs.get('p2_duration_sec')
        self.p1_manual_list = kwargs.get('p1_manual_list')
        self.p2_manual_list = kwargs.get('p2_manual_list')


class TestAutoScheduleCalculation:
    """Test auto mode schedule calculation"""
    
    def test_p1_calculation(self):
        """Test P1 event is calculated correctly"""
        zone_config = {
            'p1_duration_sec': 120,
            'p2_event_count': 0,
            'p2_duration_sec': 0
        }
        
        global_settings = GlobalTimingSettings(
            lights_on_time=time(8, 0),
            lights_off_time=time(20, 0),
            p1_start_delay_minutes=30,
            p2_start_delay_minutes=60,
            p2_end_buffer_minutes=30
        )
        
        target_date = datetime(2024, 1, 15, 7, 0)
        events = calculate_auto_schedule(zone_config, global_settings, target_date)
        
        assert len(events) == 1
        assert events[0].event_type == 'P1'
        assert events[0].duration_seconds == 120
        assert events[0].time == datetime(2024, 1, 15, 8, 30)
    
    def test_p2_distribution(self):
        """Test P2 events are distributed evenly"""
        zone_config = {
            'p1_duration_sec': 0,
            'p2_event_count': 3,
            'p2_duration_sec': 90
        }
        
        global_settings = GlobalTimingSettings(
            lights_on_time=time(8, 0),
            lights_off_time=time(20, 0),
            p1_start_delay_minutes=30,
            p2_start_delay_minutes=60,
            p2_end_buffer_minutes=60
        )
        
        target_date = datetime(2024, 1, 15, 7, 0)
        events = calculate_auto_schedule(zone_config, global_settings, target_date)
        
        assert len(events) == 3
        assert all(e.event_type == 'P2' for e in events)
        assert all(e.duration_seconds == 90 for e in events)
        
        # P2 start: 8:00 + 60min = 9:00
        # P2 end: 20:00 - 60min = 19:00
        # Window: 10 hours = 600 minutes
        # Spacing: 600 / 3 = 200 minutes
        assert events[0].time == datetime(2024, 1, 15, 9, 0)
        assert events[1].time == datetime(2024, 1, 15, 12, 20)
        assert events[2].time == datetime(2024, 1, 15, 15, 40)
    
    def test_combined_p1_and_p2(self):
        """Test both P1 and P2 events are calculated"""
        zone_config = {
            'p1_duration_sec': 120,
            'p2_event_count': 2,
            'p2_duration_sec': 60
        }
        
        global_settings = GlobalTimingSettings(
            lights_on_time=time(8, 0),
            lights_off_time=time(20, 0),
            p1_start_delay_minutes=30,
            p2_start_delay_minutes=120,
            p2_end_buffer_minutes=30
        )
        
        target_date = datetime(2024, 1, 15, 7, 0)
        events = calculate_auto_schedule(zone_config, global_settings, target_date)
        
        assert len(events) == 3
        assert events[0].event_type == 'P1'
        assert events[1].event_type == 'P2'
        assert events[2].event_type == 'P2'


class TestManualScheduleParsing:
    """Test manual schedule parsing"""
    
    def test_parse_valid_schedule(self):
        """Test parsing valid manual schedule"""
        schedule_text = "08:30.120\n14:15.90"
        target_date = datetime(2024, 1, 15, 7, 0)
        
        events = parse_manual_schedule(schedule_text, 'P1', target_date)
        
        assert len(events) == 2
        assert events[0].time == datetime(2024, 1, 15, 8, 30)
        assert events[0].duration_seconds == 120
        assert events[1].time == datetime(2024, 1, 15, 14, 15)
        assert events[1].duration_seconds == 90
    
    def test_parse_empty_schedule(self):
        """Test parsing empty schedule returns empty list"""
        events = parse_manual_schedule("", 'P1')
        assert len(events) == 0
        
        events = parse_manual_schedule(None, 'P1')
        assert len(events) == 0
    
    def test_parse_invalid_format(self):
        """Test parsing invalid format raises error"""
        with pytest.raises(ManualScheduleParseError):
            parse_manual_schedule("invalid", 'P1')
        
        with pytest.raises(ManualScheduleParseError):
            parse_manual_schedule("25:00.60", 'P1')
        
        with pytest.raises(ManualScheduleParseError):
            parse_manual_schedule("08:60.60", 'P1')
    
    def test_validate_format(self):
        """Test manual schedule format validation"""
        valid, error = validate_manual_schedule_format("08:30.120")
        assert valid is True
        assert error is None
        
        valid, error = validate_manual_schedule_format("08:30.120\n14:15.90")
        assert valid is True
        
        valid, error = validate_manual_schedule_format("invalid")
        assert valid is False
        assert error is not None


class TestNextRunTimeCalculation:
    """Test next run time calculation"""
    
    def test_auto_mode_next_run(self):
        """Test next run calculation for auto mode zone"""
        zone = MockZone(
            zone_id=1,
            name="Test Zone",
            mode='auto',
            p1_duration_sec=120,
            p2_event_count=2,
            p2_duration_sec=60
        )
        
        global_settings = GlobalTimingSettings(
            lights_on_time=time(8, 0),
            lights_off_time=time(20, 0),
            p1_start_delay_minutes=30,
            p2_start_delay_minutes=120,
            p2_end_buffer_minutes=30
        )
        
        # Current time before first event
        current_time = datetime(2024, 1, 15, 7, 0)
        next_run = get_next_run_time(zone, global_settings, current_time)
        
        assert next_run is not None
        assert next_run == datetime(2024, 1, 15, 8, 30)
    
    def test_manual_mode_next_run(self):
        """Test next run calculation for manual mode zone"""
        zone = MockZone(
            zone_id=1,
            name="Test Zone",
            mode='manual',
            p1_manual_list="08:30.120",
            p2_manual_list="14:15.90\n18:00.60"
        )
        
        # Current time before first event
        current_time = datetime(2024, 1, 15, 7, 0)
        next_run = get_next_run_time(zone, None, current_time)
        
        assert next_run is not None
        assert next_run == datetime(2024, 1, 15, 8, 30)
        
        # Current time after first event
        current_time = datetime(2024, 1, 15, 10, 0)
        next_run = get_next_run_time(zone, None, current_time)
        
        assert next_run is not None
        assert next_run == datetime(2024, 1, 15, 14, 15)
    
    def test_no_upcoming_events_rolls_to_tomorrow(self):
        """Test that calculation rolls to next day when no events today"""
        zone = MockZone(
            zone_id=1,
            name="Test Zone",
            mode='manual',
            p1_manual_list="08:30.120",
            p2_manual_list=""
        )
        
        # Current time after all events
        current_time = datetime(2024, 1, 15, 22, 0)
        next_run = get_next_run_time(zone, None, current_time)
        
        assert next_run is not None
        assert next_run == datetime(2024, 1, 16, 8, 30)
