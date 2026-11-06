import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import WebSocket

from services.api.models import (
    SensorReading, Device, Room, MeasurementType, DataProvenance, CalibrationQuality
)
from services.api.schemas import SensorReadingCreate

# Active WebSocket connections for real-time telemetry streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.discard(connection)

ws_manager = ConnectionManager()

class IngestionService:
    @staticmethod
    def normalize_unit_and_value(
        measurement_type: MeasurementType,
        value: float,
        unit: str
    ) -> tuple[float, str]:
        """
        Normalizes sensor readings into standard canonical units:
        - Temperature -> °C
        - PM1/2.5/10 -> µg/m³
        - Pressure -> hPa
        - CO2/eCO2 -> ppm
        - Humidity -> %RH
        """
        unit_lower = unit.strip().lower()
        
        if measurement_type == MeasurementType.TEMPERATURE:
            if unit_lower in ["°f", "f", "fahrenheit"]:
                # Convert F to C
                celsius = (value - 32.0) * 5.0 / 9.0
                return round(celsius, 2), "°C"
            return round(value, 2), "°C"
            
        elif measurement_type in [MeasurementType.PM1, MeasurementType.PM25, MeasurementType.PM10]:
            if unit_lower in ["mg/m3", "mg/m³"]:
                return round(value * 1000.0, 2), "µg/m³"
            return round(value, 2), "µg/m³"
            
        elif measurement_type == MeasurementType.PRESSURE:
            if unit_lower in ["pa"]:
                return round(value / 100.0, 2), "hPa"
            elif unit_lower in ["bar"]:
                return round(value * 1000.0, 2), "hPa"
            return round(value, 2), "hPa"
            
        elif measurement_type in [MeasurementType.CO2, MeasurementType.ECO2]:
            return round(value, 1), "ppm"
            
        elif measurement_type == MeasurementType.HUMIDITY:
            return round(value, 1), "%RH"
            
        elif measurement_type in [MeasurementType.VOC_INDEX, MeasurementType.NOX_INDEX]:
            return round(value, 1), "index"
            
        elif measurement_type in [MeasurementType.VOC_RAW, MeasurementType.GAS_RESISTANCE]:
            return round(value, 1), "Ω"
            
        return round(value, 2), unit

    @staticmethod
    async def ingest_reading(
        db: AsyncSession,
        reading_in: SensorReadingCreate,
        broadcast: bool = True
    ) -> SensorReading:
        # Enforce Rule 3 & Data Integrity Rule: eCO2 must never be labeled as direct CO2
        if reading_in.measurement_type == MeasurementType.CO2 and reading_in.provenance == DataProvenance.ESTIMATED:
            reading_in.measurement_type = MeasurementType.ECO2

        # 1. Normalize units and values
        norm_val, norm_unit = IngestionService.normalize_unit_and_value(
            reading_in.measurement_type,
            reading_in.value,
            reading_in.unit
        )

        # 2. Check for duplicate reading (same device, sensor, timestamp, measurement_type)
        existing = await db.execute(
            select(SensorReading).where(
                SensorReading.device_id == reading_in.device_id,
                SensorReading.sensor_id == reading_in.sensor_id,
                SensorReading.timestamp == reading_in.timestamp,
                SensorReading.measurement_type == reading_in.measurement_type
            )
        )
        existing_reading = existing.scalars().first()
        if existing_reading:
            # Duplicate reading - return existing deduplicated record
            return existing_reading

        # 3. Create canonical reading object
        reading = SensorReading(
            device_id=reading_in.device_id,
            sensor_id=reading_in.sensor_id,
            timestamp=reading_in.timestamp,
            measurement_type=reading_in.measurement_type,
            value=norm_val,
            unit=norm_unit,
            provenance=reading_in.provenance,
            raw_value=reading_in.raw_value if reading_in.raw_value is not None else reading_in.value,
            calibration_quality=reading_in.calibration_quality,
            source_integration=reading_in.source_integration,
            ingestion_timestamp=datetime.utcnow()
        )
        db.add(reading)

        # 4. Update Device last_seen_at and online status
        device_result = await db.execute(
            select(Device).where(Device.id == reading_in.device_id)
        )
        device = device_result.scalars().first()
        if device:
            device.last_seen_at = datetime.utcnow()
            device.is_online = True

        await db.commit()
        await db.refresh(reading)

        # 5. Broadcast to real-time subscribers
        if broadcast:
            reading_dict = {
                "type": "new_reading",
                "data": {
                    "id": reading.id,
                    "device_id": reading.device_id,
                    "sensor_id": reading.sensor_id,
                    "timestamp": reading.timestamp.isoformat(),
                    "measurement_type": reading.measurement_type.value,
                    "value": reading.value,
                    "unit": reading.unit,
                    "provenance": reading.provenance.value,
                    "calibration_quality": reading.calibration_quality.value,
                    "source_integration": reading.source_integration,
                    "device_name": device.name if device else "Unknown Device",
                    "room_id": device.room_id if device else None
                }
            }
            await ws_manager.broadcast(reading_dict)

        return reading

    @staticmethod
    async def get_latest_readings_for_room(
        db: AsyncSession,
        room_id: str
    ) -> List[Dict[str, Any]]:
        """Returns the most recent reading for each measurement type in a room."""
        # Find all devices in this room
        devices_res = await db.execute(select(Device).where(Device.room_id == room_id))
        devices = devices_res.scalars().all()
        if not devices:
            return []

        device_ids = [d.id for d in devices]
        
        # Query readings
        readings_res = await db.execute(
            select(SensorReading)
            .where(SensorReading.device_id.in_(device_ids))
            .order_by(SensorReading.timestamp.desc())
            .limit(100)
        )
        readings = readings_res.scalars().all()

        # Deduplicate latest per measurement type
        latest_by_type: Dict[str, Any] = {}
        now = datetime.utcnow()

        for r in readings:
            m_type = r.measurement_type.value
            if m_type not in latest_by_type:
                # Check staleness: if reading older than 5 minutes
                age_seconds = (now - r.timestamp).total_seconds()
                is_stale = age_seconds > 300
                
                latest_by_type[m_type] = {
                    "id": r.id,
                    "measurement_type": m_type,
                    "value": r.value,
                    "unit": r.unit,
                    "timestamp": r.timestamp.isoformat(),
                    "provenance": r.provenance.value,
                    "calibration_quality": r.calibration_quality.value,
                    "is_stale": is_stale,
                    "device_id": r.device_id,
                    "source_integration": r.source_integration
                }

        return list(latest_by_type.values())

