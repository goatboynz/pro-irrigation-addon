"""
Unit tests for database models.

Tests the database models including:
- Pump model creation and relationships
- Zone model creation and relationships
- GlobalSettings model
- Database constraints and cascades
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


class TestPumpModel:
    """Test Pump model"""
    
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
        assert pump.created_at is not None
        assert pump.updated_at is not None
    
    def test_pump_zones_relationship(self, db_session: Session):
        """Test pump-zones relationship"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
        db_session.add(pump)
        db_session.commit()
        db_session.refresh(pump)
        
        # Add zones to pump
        zone1 = Zone(
            pump_id=pump.id,
            name="Zone 1",
            switch_entity="switch.zone_1",
            mode="auto",
            p1_duration_sec=120,
            p2_event_count=2,
            p2_duration_sec=60
        )
        
        zone2 = Zone(
            pump_id=pump.id,
            name="Zone 2",
            switch_entity="switch.zone_2",
            mode="manual",
            p1_manual_list="08:30.120",
            p2_manual_list="14:00.90"
        )
        
        db_session.add(zone1)
        db_session.add(zone2)
        db_session.commit()
        
        # Refresh pump to load zones
        db_session.refresh(pump)
        
        assert len(pump.zones) == 2
        assert pump.zones[0].name in ["Zone 1", "Zone 2"]
        assert pump.zones[1].name in ["Zone 1", "Zone 2"]
    
    def test_pump_cascade_delete(self, db_session: Session):
        """Test that deleting a pump cascades to zones"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
        db_session.add(pump)
        db_session.commit()
        db_session.refresh(pump)
        
        # Add zone to pump
        zone = Zone(
            pump_id=pump.id,
            name="Zone 1",
            switch_entity="switch.zone_1",
            mode="auto",
            p1_duration_sec=120
        )
        
        db_session.add(zone)
        db_session.commit()
        
        zone_id = zone.id
        
        # Delete pump
        db_session.delete(pump)
        db_session.commit()
        
        # Verify zone was also deleted
        deleted_zone = db_session.query(Zone).filter(Zone.id == zone_id).first()
        assert deleted_zone is None


class TestZoneModel:
    """Test Zone model"""
    
    def test_create_auto_mode_zone(self, db_session: Session):
        """Test creating an auto mode zone"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
        db_session.add(pump)
        db_session.commit()
        
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
        assert zone.pump_id == pump.id
        assert zone.name == "Auto Zone"
        assert zone.switch_entity == "switch.auto_zone"
        assert zone.mode == "auto"
        assert zone.p1_duration_sec == 120
        assert zone.p2_event_count == 3
        assert zone.p2_duration_sec == 90
        assert zone.enabled is True
        assert zone.created_at is not None
    
    def test_create_manual_mode_zone(self, db_session: Session):
        """Test creating a manual mode zone"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
        db_session.add(pump)
        db_session.commit()
        
        zone = Zone(
            pump_id=pump.id,
            name="Manual Zone",
            switch_entity="switch.manual_zone",
            mode="manual",
            p1_manual_list="08:30.120\n10:00.90",
            p2_manual_list="14:00.60\n16:30.75",
            enabled=True
        )
        
        db_session.add(zone)
        db_session.commit()
        db_session.refresh(zone)
        
        assert zone.id is not None
        assert zone.mode == "manual"
        assert zone.p1_manual_list == "08:30.120\n10:00.90"
        assert zone.p2_manual_list == "14:00.60\n16:30.75"
    
    def test_zone_pump_relationship(self, db_session: Session):
        """Test zone-pump relationship"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
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
        
        # Access pump through relationship
        assert zone.pump is not None
        assert zone.pump.id == pump.id
        assert zone.pump.name == "Test Pump"
    
    def test_zone_enabled_default(self, db_session: Session):
        """Test that zone enabled defaults to True"""
        pump = Pump(
            name="Test Pump",
            lock_entity="input_boolean.pump_1_lock"
        )
        
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
        db_session.refresh(zone)
        
        assert zone.enabled is True


class TestGlobalSettingsModel:
    """Test GlobalSettings model"""
    
    def test_create_global_settings(self, db_session: Session):
        """Test creating global settings"""
        settings = GlobalSettings(
            lights_on_entity="input_datetime.lights_on",
            lights_off_entity="input_datetime.lights_off",
            p1_delay_entity="input_number.p1_delay",
            p2_delay_entity="input_number.p2_delay",
            p2_buffer_entity="input_number.p2_buffer",
            feed_notes="Test feed schedule notes"
        )
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        assert settings.id is not None
        assert settings.lights_on_entity == "input_datetime.lights_on"
        assert settings.lights_off_entity == "input_datetime.lights_off"
        assert settings.p1_delay_entity == "input_number.p1_delay"
        assert settings.p2_delay_entity == "input_number.p2_delay"
        assert settings.p2_buffer_entity == "input_number.p2_buffer"
        assert settings.feed_notes == "Test feed schedule notes"
        assert settings.updated_at is not None
    
    def test_update_global_settings(self, db_session: Session):
        """Test updating global settings"""
        settings = GlobalSettings(
            lights_on_entity="input_datetime.lights_on",
            feed_notes="Original notes"
        )
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        original_updated_at = settings.updated_at
        
        # Update settings
        settings.feed_notes = "Updated notes"
        settings.p1_delay_entity = "input_number.new_p1_delay"
        
        db_session.commit()
        db_session.refresh(settings)
        
        assert settings.feed_notes == "Updated notes"
        assert settings.p1_delay_entity == "input_number.new_p1_delay"
    
    def test_global_settings_nullable_fields(self, db_session: Session):
        """Test that global settings fields can be null"""
        settings = GlobalSettings()
        
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)
        
        assert settings.id is not None
        assert settings.lights_on_entity is None
        assert settings.lights_off_entity is None
        assert settings.p1_delay_entity is None
        assert settings.p2_delay_entity is None
        assert settings.p2_buffer_entity is None
        assert settings.feed_notes is None
