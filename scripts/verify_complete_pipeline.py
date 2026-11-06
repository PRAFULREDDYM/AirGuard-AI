import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.future import select

from services.api.database import init_db, AsyncSessionLocal
from services.api.models import (
    Device, Home, Room, SensorReading, AutomationRule, AutomationExecution,
    EnvironmentalEvent, IntegrationType, MeasurementType, DataProvenance
)
from services.api.schemas import SensorReadingCreate
from services.ingestion.service import IngestionService
from services.automation.engine import AutomationEngine
from services.ml_environment.anomaly import AnomalyDetector
from services.ml_molecular.service import molecular_odor_pipeline

async def verify_complete_chain():
    print("=" * 70)
    print("AIRGUARD AI — FULL PIPELINE VERIFICATION")
    print("=" * 70)

    await init_db()

    async with AsyncSessionLocal() as db:
        # STEP 1: SENSOR SETUP
        print("\n[STEP 1] SENSOR SETUP:")
        home = Home(name="Verification Residence", owner_id="user_verif_01")
        db.add(home)
        await db.commit()
        await db.refresh(home)

        room = Room(home_id=home.id, name="Living Room", room_type="living_room", target_pm25=12.0)
        db.add(room)
        await db.commit()
        await db.refresh(room)

        monitor = Device(
            home_id=home.id,
            room_id=room.id,
            name="AirGradient ONE Monitor",
            manufacturer="AirGradient",
            model="ONE v3.1",
            connection_protocol=IntegrationType.AIRGRADIENT,
            is_controllable=False,
            is_online=True
        )
        purifier = Device(
            home_id=home.id,
            room_id=room.id,
            name="Smart HEPA Purifier",
            manufacturer="AirGuard Systems",
            model="CleanAir-400",
            connection_protocol=IntegrationType.SIMULATION,
            is_controllable=True,
            automation_authorized=True,
            manual_override=False,
            is_online=True
        )
        db.add_all([monitor, purifier])
        await db.commit()
        await db.refresh(monitor)
        await db.refresh(purifier)

        rule = AutomationRule(
            home_id=home.id,
            room_id=room.id,
            name="Auto High Speed on Particle Spike",
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
        print(f"  ✓ Sensor Created: {monitor.name} (id={monitor.id[:8]}...)")
        print(f"  ✓ Actuator Created: {purifier.name} (Authorized: {purifier.automation_authorized})")
        print(f"  ✓ Automation Rule Active: IF PM2.5 > {rule.trigger_config['threshold']} -> set_speed high")

        # STEP 2 & 3: SENSOR TELEMETRY & BACKEND INGESTION -> DATABASE PERSISTENCE
        print("\n[STEP 2 & 3] SENSOR TELEMETRY -> BACKEND INGESTION -> DATABASE:")
        raw_telemetry = SensorReadingCreate(
            device_id=monitor.id,
            sensor_id="pm02_laser",
            timestamp=datetime.utcnow(),
            measurement_type=MeasurementType.PM25,
            value=0.048,           # in mg/m³
            unit="mg/m³",          # Unit normalization required!
            provenance=DataProvenance.MEASURED,
            source_integration="airgradient"
        )
        ingested_reading = await IngestionService.ingest_reading(db, raw_telemetry, broadcast=False)
        print(f"  ✓ Raw input: 0.048 mg/m³")
        print(f"  ✓ Normalized in DB: {ingested_reading.value} {ingested_reading.unit} (Provenance: {ingested_reading.provenance.value})")
        assert ingested_reading.value == 48.0
        assert ingested_reading.unit == "µg/m³"

        # STEP 4: AI & RULES ENGINE EVALUATION
        print("\n[STEP 4] AI & RULES ENGINE:")
        event = await AnomalyDetector.evaluate_reading(db, ingested_reading)
        assert event is not None
        print(f"  ✓ Event Detected: {event.title} (Severity: {event.severity.value}, Score: {event.anomaly_score})")

        # STEP 5: AUTOMATION DISPATCH & AUTHORIZATION CHECK
        print("\n[STEP 5 & 6] DASHBOARD AUTOMATION -> AUTHORIZED DEVICE COMMAND -> CONFIRMATION:")
        execs = await AutomationEngine.evaluate_rules_for_reading(db, ingested_reading)
        assert len(execs) == 1
        print(f"  ✓ Dispatched Command: {execs[0].command} on Device {execs[0].device_id[:8]}...")
        print(f"  ✓ Status: {execs[0].status}")
        print(f"  ✓ Reason: {execs[0].reason}")

        # STEP 7: MOLECULAR AI SEPARATION CHECK
        print("\n[STEP 7] MOLECULAR AI INDEPENDENCE TEST:")
        mol_res = molecular_odor_pipeline.predict_odor_descriptors("CC(=O)OCCC(C)C") # Isoamyl acetate
        print(f"  ✓ SMILES: {mol_res['smiles']}")
        print(f"  ✓ Engine: {mol_res['inference_engine']}")
        print(f"  ✓ Top Descriptors: {[d['descriptor'] for d in mol_res['predicted_descriptors'][:3]]}")
        print(f"  ✓ Disclaimer: {mol_res['warning']}")

        print("\n" + "=" * 70)
        print("ALL VERIFICATION STAGES COMPLETED SUCCESSFULLY WITH CODE 0")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(verify_complete_chain())

