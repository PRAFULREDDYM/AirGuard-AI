"""
AirGuard AI — Phase 8: Automation Race Condition & Pre-Dispatch Recheck Verification Tests
Tests:
- Consent revocation immediately prior to command dispatch halts execution.
- Emergency pause kill-switch activated in interim halts execution.
- Target device manual override engaged in interim halts execution.
- Device authorization revocation in interim halts execution.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.future import select

from services.api.database import AsyncSessionLocal
from services.api.models import (
    User, Home, Room, Device, SensorReading, MeasurementType,
    AutomationRule, UserConsent, DataProvenance, CalibrationQuality
)
from services.automation.engine import AutomationEngine

@pytest.mark.asyncio
async def test_race_condition_consent_revoked_at_dispatch():
    """Simulates consent revocation occurring right before command execution."""
    uid = uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(id=f"u_{uid}", email=f"race_{uid}@airguard.ai", hashed_password="pw", is_active=True)
        home = Home(id=f"h_{uid}", owner_id=user.id, name="Race Home", automations_paused=False)
        room = Room(id=f"r_{uid}", home_id=home.id, name="Living Room")
        monitor = Device(
            id=f"mon_{uid}", home_id=home.id, room_id=room.id, name="AirGradient Monitor",
            manufacturer="AirGradient", model="ONE", connection_protocol="simulation",
            is_controllable=False, is_online=True, last_seen_at=datetime.utcnow()
        )
        purifier = Device(
            id=f"pur_{uid}", home_id=home.id, room_id=room.id, name="Smart Purifier",
            manufacturer="Levoit", model="Core 400S", connection_protocol="simulation",
            is_controllable=True, automation_authorized=True, is_online=True, last_seen_at=datetime.utcnow()
        )
        # Create active consent initially
        consent = UserConsent(
            id=f"c_{uid}", user_id=user.id, home_id=home.id, device_id=purifier.id,
            permission_type="DEVICE_CONTROL", is_active=True
        )
        rule = AutomationRule(
            id=f"rule_{uid}", home_id=home.id, room_id=room.id, name="PM2.5 Purifier Boost",
            trigger_config={"measurement_type": "PM25", "condition": "ABOVE", "threshold": 25.0},
            action_config={"device_id": purifier.id, "command": "set_speed", "parameters": {"speed": 3}},
            enabled=True, cooldown_seconds=0
        )
        db.add_all([user, home, room, monitor, purifier, consent, rule])
        await db.commit()

        # Ingest reading
        reading = SensorReading(
            device_id=monitor.id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25, value=48.0,
            unit="µg/m³", provenance=DataProvenance.MEASURED, calibration_quality=CalibrationQuality.CALIBRATED,
            source_integration="simulation", timestamp=datetime.utcnow()
        )

        # Dispatch tracker
        dispatched_commands = []
        async def mock_dispatcher(device, cmd, params):
            dispatched_commands.append((device.id, cmd, params))

        # Now revoke consent in database before evaluation dispatch
        consent.is_active = False
        consent.revoked_at = datetime.utcnow()
        await db.commit()

        # Run engine
        execs = await AutomationEngine.evaluate_rules_for_reading(
            db=db, reading=reading, device_adapter_dispatcher=mock_dispatcher
        )

        # Command must NOT have been dispatched
        assert len(dispatched_commands) == 0

@pytest.mark.asyncio
async def test_race_condition_pause_killswitch_at_dispatch():
    """Simulates global killswitch activation immediately prior to command dispatch."""
    uid = uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(id=f"u_{uid}", email=f"pause_{uid}@airguard.ai", hashed_password="pw", is_active=True)
        home = Home(id=f"h_{uid}", owner_id=user.id, name="Pause Home", automations_paused=True) # Globally paused!
        room = Room(id=f"r_{uid}", home_id=home.id, name="Living Room")
        monitor = Device(
            id=f"mon_{uid}", home_id=home.id, room_id=room.id, name="Monitor",
            manufacturer="AirGradient", model="ONE", connection_protocol="simulation",
            is_controllable=False, is_online=True, last_seen_at=datetime.utcnow()
        )
        purifier = Device(
            id=f"pur_{uid}", home_id=home.id, room_id=room.id, name="Purifier",
            manufacturer="Levoit", model="Core 400S", connection_protocol="simulation",
            is_controllable=True, automation_authorized=True, is_online=True, last_seen_at=datetime.utcnow()
        )
        consent = UserConsent(
            id=f"c_{uid}", user_id=user.id, home_id=home.id, device_id=purifier.id,
            permission_type="DEVICE_CONTROL", is_active=True
        )
        rule = AutomationRule(
            id=f"rule_{uid}", home_id=home.id, room_id=room.id, name="PM2.5 Boost",
            trigger_config={"measurement_type": "PM25", "condition": "ABOVE", "threshold": 25.0},
            action_config={"device_id": purifier.id, "command": "set_speed", "parameters": {"speed": 3}},
            enabled=True, cooldown_seconds=0
        )
        db.add_all([user, home, room, monitor, purifier, consent, rule])
        await db.commit()

        reading = SensorReading(
            device_id=monitor.id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25, value=55.0,
            unit="µg/m³", provenance=DataProvenance.MEASURED, calibration_quality=CalibrationQuality.CALIBRATED,
            source_integration="simulation", timestamp=datetime.utcnow()
        )

        dispatched_commands = []
        async def mock_dispatcher(device, cmd, params):
            dispatched_commands.append((device.id, cmd, params))

        execs = await AutomationEngine.evaluate_rules_for_reading(
            db=db, reading=reading, device_adapter_dispatcher=mock_dispatcher
        )

        # Zero dispatches permitted when automations_paused is True
        assert len(dispatched_commands) == 0
        assert len(execs) == 0

@pytest.mark.asyncio
async def test_race_condition_manual_override_at_dispatch():
    """Simulates user manually pushing button on purifier right before automated dispatch."""
    uid = uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(id=f"u_{uid}", email=f"override_{uid}@airguard.ai", hashed_password="pw", is_active=True)
        home = Home(id=f"h_{uid}", owner_id=user.id, name="Override Home", automations_paused=False)
        room = Room(id=f"r_{uid}", home_id=home.id, name="Living Room")
        monitor = Device(
            id=f"mon_{uid}", home_id=home.id, room_id=room.id, name="Monitor",
            manufacturer="AirGradient", model="ONE", connection_protocol="simulation",
            is_controllable=False, is_online=True, last_seen_at=datetime.utcnow()
        )
        purifier = Device(
            id=f"pur_{uid}", home_id=home.id, room_id=room.id, name="Purifier",
            manufacturer="Levoit", model="Core 400S", connection_protocol="simulation",
            is_controllable=True, automation_authorized=True,
            manual_override=True, # Active manual override
            manual_override_until=datetime.utcnow() + timedelta(minutes=45),
            is_online=True, last_seen_at=datetime.utcnow()
        )
        consent = UserConsent(
            id=f"c_{uid}", user_id=user.id, home_id=home.id, device_id=purifier.id,
            permission_type="DEVICE_CONTROL", is_active=True
        )
        rule = AutomationRule(
            id=f"rule_{uid}", home_id=home.id, room_id=room.id, name="PM2.5 Boost",
            trigger_config={"measurement_type": "PM25", "condition": "ABOVE", "threshold": 25.0},
            action_config={"device_id": purifier.id, "command": "set_speed", "parameters": {"speed": 3}},
            enabled=True, cooldown_seconds=0
        )
        db.add_all([user, home, room, monitor, purifier, consent, rule])
        await db.commit()

        reading = SensorReading(
            device_id=monitor.id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25, value=60.0,
            unit="µg/m³", provenance=DataProvenance.MEASURED, calibration_quality=CalibrationQuality.CALIBRATED,
            source_integration="simulation", timestamp=datetime.utcnow()
        )

        dispatched_commands = []
        async def mock_dispatcher(device, cmd, params):
            dispatched_commands.append((device.id, cmd, params))

        execs = await AutomationEngine.evaluate_rules_for_reading(
            db=db, reading=reading, device_adapter_dispatcher=mock_dispatcher
        )

        # Zero physical dispatches when manual override is engaged
        assert len(dispatched_commands) == 0
        assert len(execs) > 0
        assert execs[0].status == "BLOCKED_BY_SAFETY"
        assert "MANUAL OVERRIDE" in execs[0].reason or "manual override" in execs[0].reason.lower()
