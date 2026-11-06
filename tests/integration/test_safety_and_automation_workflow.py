import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from services.api.database import init_db, AsyncSessionLocal
from services.api.models import Device, Home, Room, AutomationRule, AutomationExecution, IntegrationType, MeasurementType
from services.api.schemas import SensorReadingCreate
from services.ingestion.service import IngestionService
from services.automation.engine import AutomationEngine
from services.automation.safety import SafetyEngine

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_complete_event_purifier_control_and_safety_workflow():
    async with AsyncSessionLocal() as db:
        # 1. Setup Home, Room, Monitor & Controllable Purifier
        home = Home(name="Safety Test Home", owner_id="user_safety_01")
        db.add(home)
        await db.commit()
        await db.refresh(home)

        room = Room(home_id=home.id, name="Test Chamber", room_type="living_room")
        db.add(room)
        await db.commit()
        await db.refresh(room)

        purifier = Device(
            home_id=home.id,
            room_id=room.id,
            name="AirGuard SafePurifier",
            manufacturer="AirGuard Systems",
            model="Safe-400",
            connection_protocol=IntegrationType.SIMULATION,
            is_controllable=True,
            automation_authorized=True,
            manual_override=False,
            is_online=True
        )
        db.add(purifier)
        await db.commit()
        await db.refresh(purifier)

        # 2. Create Automation Rule: PM2.5 > 35 -> set_speed high (Cooldown: 300s)
        rule = AutomationRule(
            home_id=home.id,
            room_id=room.id,
            name="Auto High Speed on Particulate Spike",
            enabled=True,
            trigger_config={
                "measurement_type": "PM25",
                "condition": "ABOVE",
                "threshold": 35.0,
                "duration_seconds": 30
            },
            action_config={
                "device_id": purifier.id,
                "command": "set_speed",
                "parameters": {"speed": "high"}
            },
            cooldown_seconds=300,
            max_executions_per_hour=4
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # 3. Simulate Event: PM2.5 rises to 52.0 µg/m³
        spike_reading = SensorReadingCreate(
            device_id=purifier.id,
            sensor_id="chamber_pm25",
            timestamp=datetime.utcnow(),
            measurement_type=MeasurementType.PM25,
            value=52.0,
            unit="µg/m³",
            provenance="SIMULATED",
            source_integration="simulation"
        )
        persisted_reading = await IngestionService.ingest_reading(db, spike_reading, broadcast=False)
        execs_1 = await AutomationEngine.evaluate_rules_for_reading(db, persisted_reading)

        assert len(execs_1) == 1
        assert execs_1[0].status == "SUCCESS"
        assert execs_1[0].command == "set_speed"
        assert "speed" in execs_1[0].parameters

        # 4. Cooldown Test: Immediate second reading with elevated PM2.5 (should NOT trigger second command)
        second_reading = SensorReadingCreate(
            device_id=purifier.id,
            sensor_id="chamber_pm25",
            timestamp=datetime.utcnow() + timedelta(seconds=10),
            measurement_type=MeasurementType.PM25,
            value=55.0,
            unit="µg/m³",
            provenance="SIMULATED",
            source_integration="simulation"
        )
        p_read_2 = await IngestionService.ingest_reading(db, second_reading, broadcast=False)
        execs_cooldown = await AutomationEngine.evaluate_rules_for_reading(db, p_read_2)
        assert len(execs_cooldown) == 0  # Cooldown active!

        # 5. Manual Override Test: User engages manual override
        purifier.manual_override = True
        rule.last_triggered_at = datetime.utcnow() - timedelta(seconds=400) # Reset cooldown
        await db.commit()

        third_reading = SensorReadingCreate(
            device_id=purifier.id,
            sensor_id="chamber_pm25",
            timestamp=datetime.utcnow() + timedelta(seconds=410),
            measurement_type=MeasurementType.PM25,
            value=60.0,
            unit="µg/m³",
            provenance="SIMULATED",
            source_integration="simulation"
        )
        p_read_3 = await IngestionService.ingest_reading(db, third_reading, broadcast=False)
        execs_override = await AutomationEngine.evaluate_rules_for_reading(db, p_read_3)
        assert len(execs_override) == 1
        assert execs_override[0].status == "BLOCKED_BY_SAFETY"
        assert "MANUAL OVERRIDE" in execs_override[0].reason

        # 6. Safety Constraint: Prohibited Combustible Gas / Ozone Command Blocks
        is_allowed, safety_reason = SafetyEngine.validate_automation_action(
            device=purifier,
            command="set_speed",
            parameters={"speed": "high"},
            suspected_hazard="combustible_gas"
        )
        assert not is_allowed
        assert "SAFETY VIOLATION" in safety_reason
        assert "combustible_gas" in safety_reason

