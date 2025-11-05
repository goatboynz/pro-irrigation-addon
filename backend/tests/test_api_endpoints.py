"""
Unit tests for API endpoint logic.

Tests the database operations and business logic for:
- Pump CRUD operations
- Zone CRUD operations
- Global settings operations
- Data validation
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models.database import Base
from models.pump import Pump
from models.zone import Zone
from models.global_settings import GlobalSettings

# Import calculator function directly to avoid circular imports
import importlib.util
calc_spec = importlib.util.spec_from_file_location("calculator", Path(__file__).parent.parent / "services" / "calculator.py")
calculator = importlib.util.module_from_spec(calc_spec)
calc_spec.loader.exec_module(calculator)
validate_manual_schedule_format = calculator.validate_manual_schedule_format


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Use in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


class TestPumpOperations:
    """Test pump database operations"""
    
    def test_create_pump(self, db_session: Session):
        """Test creating a pump"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
        db_session.add(pump)
        db_session.commit()
        db_session.refresh(pump)
        
        assert pump.id is not None
        assert pump.name == "Test Pump"
        assert pump.lock_entity == "input_boolean.pump_1_lock"
    
    def test_list_pumps(self, db_session: Session):
        """Test listing all pumps"""
        # Create test pumps
        pump1 = Pump(name="Pump 1", lock_entity="input_boolean.pump_1_lock")
        pump2 = Pump(name="Pump 2", lock_entity="input_boolean.pump_2_lock")
        
        db_session.add(pump1)
        db_session.add(pump2)
        db_session.commit()
        
        # Query all pumps
        pumps = db_session.query(Pump).all()
        
        assert len(pumps) == 2
        assert pumps[0].name in ["Pump 1", "Pump 2"]
        assert pumps[1].name in ["Pump 1", "Pump 2"]
    
    def test_get_pump_by_id(self, db_session: Session):
        """Test getting a pump by ID"""
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        
        db_session.add(pump)
        db_session.commit()
        db_session.refresh(pump)
        
        # Query pump by ID
        found_pump = db_session.query(Pump).filter(Pump.id == pump.id).first()
        
        assert found_pump is not None
        assert found_pump.id == pump.id
        assert found_pump.name == "Test Pump"
    
    def test_get_pump_not_found(self, db_session: Session):
        """Test querying non-existent pump"""
        pump = db_session.query(Pump).filter(Pump.id == 999).first()
        
        assert pump is None
    
    def test_update_pump(self, db_session: Session):
        """Test updating a pump"""
        pump = Pump(name="Original Name", lock_entity="input_boolean.pump_lock")
        
        db_session.add(pump)
        db_session.commit()
        db_session.refresh(pump)
        
        # Update pump
        pump.name = "Updated Name"
        db_session.commit()
        db_session.refresh(pump)
        
        assert pump.name == "Updated Name"
        assert pump.lock_entity == "input_boolean.pump_lock"
    
    def test_delete_pump(self, db_session: Session):
        """Test deleting a pump"""
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        
        db_session.add(pump)
        db_session.commit()
        
        pump_id = pump.id
        
        # Delete pump
        db_session.delete(pump)
        db_session.commit()
        
        # Verify pump is deleted
        deleted_pump = db_session.query(Pump).filter(Pump.id == pump_id).first()
        assert deleted_pump is None


class TestZoneOperations:
    """Test zone database operations"""
    
    def test_create_auto_zone(self, db_session: Session):
        """Test creating an auto mode zone"""
        # Create pump first
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        # Create zone
        zone = Zone(
            pump_id=pump.id,
            name="Auto Zone",
            switch_entity="switch.auto_zone",
            mode="auto",
            p1_duration_sec=120,
            p2_event_count=3,
            p2_duration_sec=90,
            enabled=True
        )
        
        db_session.add(zone)
        db_session.commit()
        db_session.refresh(zone)
        
        assert zone.id is not None
        assert zone.name == "Auto Zone"
        assert zone.mode == "auto"
        assert zone.p1_duration_sec == 120
        assert zone.p2_event_count == 3
        assert zone.p2_duration_sec == 90
    
    def test_create_manual_zone(self, db_session: Session):
        """Test creating a manual mode zone"""
        # Create pump first
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        # Create zone
        zone = Zone(
            pump_id=pump.id,
            name="Manual Zone",
            switch_entity="switch.manual_zone",
            mode="manual",
            p1_manual_list="08:30.120",
            p2_manual_list="14:00.90\n16:30.60",
            enabled=True
        )
        
        db_session.add(zone)
        db_session.commit()
        db_session.refresh(zone)
        
        assert zone.id is not None
        assert zone.name == "Manual Zone"
        assert zone.mode == "manual"
        assert zone.p1_manual_list == "08:30.120"
        assert zone.p2_manual_list == "14:00.90\n16:30.60"
    
    def test_list_zones_for_pump(self, db_session: Session):
        """Test listing zones for a pump"""
        # Create pump
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        # Create zones
        zone1 = Zone(
            pump_id=pump.id,
            name="Zone 1",
            switch_entity="switch.zone_1",
            mode="auto",
            p1_duration_sec=120
        )
        zone2 = Zone(
            pump_id=pump.id,
            name="Zone 2",
            switch_entity="switch.zone_2",
            mode="manual",
            p1_manual_list="08:30.120"
        )
        
        db_session.add(zone1)
        db_session.add(zone2)
        db_session.commit()
        
        # Query zones for pump
        zones = db_session.query(Zone).filter(Zone.pump_id == pump.id).all()
        
        assert len(zones) == 2
        assert zones[0].name in ["Zone 1", "Zone 2"]
        assert zones[1].name in ["Zone 1", "Zone 2"]
    
    def test_get_zone_by_id(self, db_session: Session):
        """Test getting a zone by ID"""
        # Create pump and zone
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        zone = Zone(
            pump_id=pump.id,
            name="Test Zone",
            switch_entity="switch.test_zone",
            mode="auto",
            p1_duration_sec=120
        )
        
        db_session.add(zone)
        db_session.commit()
        db_session.refresh(zone)
        
        # Query zone by ID
        found_zone = db_session.query(Zone).filter(Zone.id == zone.id).first()
        
        assert found_zone is not None
        assert found_zone.id == zone.id
        assert found_zone.name == "Test Zone"
    
    def test_update_zone(self, db_session: Session):
        """Test updating a zone"""
        # Create pump and zone
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        zone = Zone(
            pump_id=pump.id,
            name="Original Zone",
            switch_entity="switch.test_zone",
            mode="auto",
            p1_duration_sec=120
        )
        
        db_session.add(zone)
        db_session.commit()
        db_session.refresh(zone)
        
        # Update zone
        zone.name = "Updated Zone"
        zone.p1_duration_sec = 180
        db_session.commit()
        db_session.refresh(zone)
        
        assert zone.name == "Updated Zone"
        assert zone.p1_duration_sec == 180
    
    def test_delete_zone(self, db_session: Session):
        """Test deleting a zone"""
        # Create pump and zone
        pump = Pump(name="Test Pump", lock_entity="input_boolean.pump_lock")
        db_session.add(pump)
        db_session.commit()
        
        zone = Zone(
            pump_id=pump.id,
            name="Test Zone",
            switch_entity="switch.test_zone",
            mode="auto"
        )
        
        db_session.add(zone)
        db_session.commit()
        
        zone_id = zone.id
        
        # Delete zone
        db_session.delete(zone)
        db_session.commit()
        
        # Verify zone is deleted
        deleted_zone = db_session.query(Zone).filter(Zone.id == zone_id).first()
        assert deleted_zone is None
    
    def test_validate_manual_schedule_format(self):
        """Test manual schedule format validation"""
        # Valid format
        valid, error = validate_manual_schedule_format("08:30.120")
        assert valid is True
        assert error is None
        
        # Invalid format
        valid, error = validate_manual_schedule_format("invalid_format")
        assert valid is False
        assert error is not None
        assert "format" in error.lower()


class TestGlobalSettingsOperations:
    """Test global settings database operations"""
    
    def test_create_global_settings(self, db_session: Session):
        """Test creating global settings"""
        settings = GlobalSettings(
            lights_on_entity="input_datetime.lights_on",
            lights_off_entity="input_datetime.lights_off",
            p1_delay_entity="input_number.p1_delay",
            p2_delay_entity="input_number.p2_delay",
            p2_buffer_entity="input_number.p2_buffer",
            feed_notes="Test feed notes"
        )
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        assert settings.id is not None
        assert settings.lights_on_entity == "input_datetime.lights_on"
        assert settings.lights_off_entity == "input_datetime.lights_off"
        assert settings.feed_notes == "Test feed notes"
    
    def test_get_or_create_settings(self, db_session: Session):
        """Test getting or creating default settings"""
        # Query settings (should not exist initially)
        settings = db_session.query(GlobalSettings).first()
        
        if not settings:
            # Create default settings
            settings = GlobalSettings()
            db_session.add(settings)
            db_session.commit()
            db_session.refresh(settings)
        
        assert settings is not None
        assert settings.id is not None
    
    def test_update_global_settings(self, db_session: Session):
        """Test updating global settings"""
        # Create settings
        settings = GlobalSettings(
            lights_on_entity="input_datetime.lights_on",
            feed_notes="Original notes"
        )
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        # Update settings
        settings.lights_off_entity = "input_datetime.lights_off"
        settings.feed_notes = "Updated notes"
        db_session.commit()
        db_session.refresh(settings)
        
        assert settings.lights_on_entity == "input_datetime.lights_on"
        assert settings.lights_off_entity == "input_datetime.lights_off"
        assert settings.feed_notes == "Updated notes"
    
    def test_partial_update_settings(self, db_session: Session):
        """Test partial update of global settings"""
        # Create settings
        settings = GlobalSettings(
            lights_on_entity="input_datetime.lights_on",
            feed_notes="Original notes"
        )
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        # Partial update (only feed_notes)
        settings.feed_notes = "Updated notes"
        db_session.commit()
        db_session.refresh(settings)
        
        # Verify lights_on_entity is unchanged
        assert settings.lights_on_entity == "input_datetime.lights_on"
        assert settings.feed_notes == "Updated notes"
