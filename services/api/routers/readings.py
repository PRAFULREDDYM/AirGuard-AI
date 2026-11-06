import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from services.api.database import get_db
from services.api.models import SensorReading, Device, Room, MeasurementType, DataProvenance, CalibrationQuality
from services.api.schemas import SensorReadingCreate, SensorReadingResponse
from services.api.security import get_current_user, get_optional_user
from services.ingestion.service import IngestionService
from services.automation.engine import AutomationEngine
from services.ml_environment.anomaly import AnomalyDetector
from services.integrations.simulation_adapter import simulation_adapter

router = APIRouter(prefix="/readings", tags=["Sensor Readings"])

@router.post("", response_model=SensorReadingResponse)
async def ingest_sensor_reading(
    reading_in: SensorReadingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests a canonical sensor reading:
    - Normalizes units
    - Deduplicates
    - Enforces provenance
    - Evaluates anomaly detection
    - Evaluates automation rules
    - Broadcasts to WebSocket clients
    """
    # 1. Ingest & Persist
    reading = await IngestionService.ingest_reading(db, reading_in, broadcast=True)

    # 2. Check for environmental anomaly / threshold
    await AnomalyDetector.evaluate_reading(db, reading)

    # 3. Evaluate automation rules
    await AutomationEngine.evaluate_rules_for_reading(db, reading)

    return SensorReadingResponse.model_validate(reading)

@router.get("", response_model=List[SensorReadingResponse])
async def query_readings(
    device_id: Optional[str] = None,
    room_id: Optional[str] = None,
    measurement_type: Optional[MeasurementType] = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=300, ge=1, le=2000),
    db: AsyncSession = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(hours=hours)
    query = select(SensorReading).where(SensorReading.timestamp >= since)

    if device_id:
        query = query.where(SensorReading.device_id == device_id)
    elif room_id:
        devs_res = await db.execute(select(Device.id).where(Device.room_id == room_id))
        dev_ids = devs_res.scalars().all()
        query = query.where(SensorReading.device_id.in_(dev_ids))

    if measurement_type:
        query = query.where(SensorReading.measurement_type == measurement_type)

    query = query.order_by(SensorReading.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()
    return [SensorReadingResponse.model_validate(r) for r in reversed(readings)]

@router.get("/export/csv")
async def export_readings_csv(
    room_id: Optional[str] = None,
    device_id: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Exports historical sensor readings as a CSV download."""
    since = datetime.utcnow() - timedelta(days=days)
    query = select(SensorReading).where(SensorReading.timestamp >= since)

    if device_id:
        query = query.where(SensorReading.device_id == device_id)
    elif room_id:
        devs_res = await db.execute(select(Device.id).where(Device.room_id == room_id))
        dev_ids = devs_res.scalars().all()
        query = query.where(SensorReading.device_id.in_(dev_ids))

    query = query.order_by(SensorReading.timestamp.asc())
    result = await db.execute(query)
    readings = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp_utc", "device_id", "sensor_id", "measurement_type",
        "value", "unit", "provenance", "raw_value", "calibration_quality", "source_integration"
    ])

    for r in readings:
        writer.writerow([
            r.timestamp.isoformat(),
            r.device_id,
            r.sensor_id,
            r.measurement_type.value,
            r.value,
            r.unit,
            r.provenance.value,
            r.raw_value if r.raw_value is not None else "",
            r.calibration_quality.value,
            r.source_integration
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=airguard_readings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.post("/simulation/tick")
async def simulation_tick(
    scenario: str = "normal",
    db: AsyncSession = Depends(get_db)
):
    """Generates a batch of synthetic readings from the simulation adapter for testing/demo."""
    simulation_adapter.set_scenario(scenario)

    # Find simulation devices
    res = await db.execute(select(Device).where(Device.connection_protocol == IntegrationType.SIMULATION))
    sim_devices = res.scalars().all()

    generated_count = 0
    for dev in sim_devices:
        readings_raw = await simulation_adapter.read_telemetry("sim_airgradient_01" if "airgradient" in dev.name.lower() else "sim_purifier_01")
        for item in readings_raw:
            reading_in = SensorReadingCreate(
                device_id=dev.id,
                sensor_id=item["sensor_id"],
                timestamp=item["timestamp"],
                measurement_type=item["measurement_type"],
                value=item["value"],
                unit=item["unit"],
                provenance=item["provenance"],
                calibration_quality=item["calibration_quality"],
                source_integration="simulation"
            )
            r = await IngestionService.ingest_reading(db, reading_in, broadcast=True)
            await AnomalyDetector.evaluate_reading(db, r)
            await AutomationEngine.evaluate_rules_for_reading(db, r)
            generated_count += 1

    return {"message": f"Generated {generated_count} simulated sensor readings.", "scenario": scenario}

