import pytest
import pytest_asyncio
import json
from datetime import datetime
from sqlalchemy.future import select

from services.api.database import init_db, AsyncSessionLocal
from services.api.models import Device, Home, Room, SensorReading, IntegrationType, MeasurementType, DataProvenance
from services.api.schemas import SensorReadingCreate
from services.ingestion.service import IngestionService
from services.integrations.mqtt_adapter import MQTTAdapter

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_mqtt_telemetry_ingestion_end_to_end():
    async with AsyncSessionLocal() as db:
        # 1. Create a home, room, and MQTT device
        home = Home(name="MQTT Test Home", owner_id="user_mqtt_01")
        db.add(home)
        await db.commit()
        await db.refresh(home)

        room = Room(home_id=home.id, name="Sensor Lab", room_type="office")
        db.add(room)
        await db.commit()
        await db.refresh(room)

        mqtt_dev = Device(
            home_id=home.id,
            room_id=room.id,
            name="ESP32 BME688 Node",
            manufacturer="DIY ESPHome",
            model="ESP32-WROOM",
            connection_protocol=IntegrationType.MQTT,
            is_controllable=False,
            is_online=True
        )
        db.add(mqtt_dev)
        await db.commit()
        await db.refresh(mqtt_dev)

        # 2. Simulate MQTT message arrival handler
        raw_payload = json.dumps({
            "pm25": 38.5,
            "co2": 720.0,
            "voc_index": 195.0,
            "temperature": 24.2,
            "humidity": 46.5
        })

        # Process payload like MQTT adapter on_message callback
        parsed = json.loads(raw_payload)
        now = datetime.utcnow()

        readings_to_ingest = [
            SensorReadingCreate(
                device_id=mqtt_dev.id,
                sensor_id="mqtt_pm25",
                timestamp=now,
                measurement_type=MeasurementType.PM25,
                value=float(parsed["pm25"]),
                unit="µg/m³",
                provenance=DataProvenance.MEASURED,
                source_integration="mqtt"
            ),
            SensorReadingCreate(
                device_id=mqtt_dev.id,
                sensor_id="mqtt_co2",
                timestamp=now,
                measurement_type=MeasurementType.CO2,
                value=float(parsed["co2"]),
                unit="ppm",
                provenance=DataProvenance.MEASURED,
                source_integration="mqtt"
            )
        ]

        ingested = []
        for r_in in readings_to_ingest:
            r = await IngestionService.ingest_reading(db, r_in, broadcast=True)
            ingested.append(r)

        assert len(ingested) == 2
        assert ingested[0].value == 38.5
        assert ingested[0].measurement_type == MeasurementType.PM25
        assert ingested[0].provenance == DataProvenance.MEASURED

        # 3. Verify Database Persistence
        db_readings = await db.execute(
            select(SensorReading).where(SensorReading.device_id == mqtt_dev.id)
        )
        persisted = db_readings.scalars().all()
        assert len(persisted) >= 2
        pm_persisted = [p for p in persisted if p.measurement_type == MeasurementType.PM25][0]
        assert pm_persisted.value == 38.5
        assert pm_persisted.source_integration == "mqtt"

        # 4. Verify Device last_seen_at was updated by IngestionService
        refreshed_dev = await db.get(Device, mqtt_dev.id)
        assert refreshed_dev.is_online is True
        assert refreshed_dev.last_seen_at is not None

