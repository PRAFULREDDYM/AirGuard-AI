import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from services.api.models import MeasurementType, DataProvenance, CalibrationQuality, IntegrationType
from services.integrations.base_adapter import (
    DeviceAdapter, DiscoveredDevice, AdapterHealth, DeviceCommand, CommandResult
)

class AirGradientAdapter:
    def __init__(self, host: str, port: int = 80):
        # host can be IP or airgradient_<serial>.local
        self.host = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"

    async def test_connection(self) -> bool:
        """Tests local HTTP connection to /measures/current."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/measures/current")
                return res.status_code == 200
        except Exception:
            return False

    async def discover(self) -> List[DiscoveredDevice]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/measures/current")
                if res.status_code != 200:
                    return []
                data = res.json()
        except Exception:
            return []

        serial = data.get("serialno", self.host)
        model = data.get("model", "AirGradient ONE")
        fw = data.get("firmware", "Unknown")

        return [
            DiscoveredDevice(
                id=f"airgradient_{serial}",
                name=f"AirGradient Monitor ({serial})",
                manufacturer="AirGradient",
                model=model,
                firmware_version=fw,
                protocol=IntegrationType.AIRGRADIENT,
                is_controllable=False,
                supported_measurements=[
                    {"type": "PM25", "unit": "µg/m³", "provenance": "MEASURED"},
                    {"type": "PM10", "unit": "µg/m³", "provenance": "MEASURED"},
                    {"type": "PM1", "unit": "µg/m³", "provenance": "MEASURED"},
                    {"type": "CO2", "unit": "ppm", "provenance": "MEASURED"},
                    {"type": "VOC_INDEX", "unit": "index", "provenance": "MEASURED"},
                    {"type": "NOX_INDEX", "unit": "index", "provenance": "MEASURED"},
                    {"type": "TEMPERATURE", "unit": "°C", "provenance": "MEASURED"},
                    {"type": "HUMIDITY", "unit": "%RH", "provenance": "MEASURED"}
                ],
                supported_controls=[]
            )
        ]

    async def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/measures/current")
                if res.status_code != 200:
                    return []
                data = res.json()
        except Exception:
            return []

        now = datetime.utcnow()
        readings = []

        # Parse documented fields
        # PM2.5 (use compensated if available)
        pm25 = data.get("pm02Compensated") if data.get("pm02Compensated") is not None else data.get("pm02")
        if pm25 is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "pm02",
                "timestamp": now,
                "measurement_type": MeasurementType.PM25,
                "value": float(pm25),
                "unit": "µg/m³",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # PM10
        if data.get("pm10") is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "pm10",
                "timestamp": now,
                "measurement_type": MeasurementType.PM10,
                "value": float(data["pm10"]),
                "unit": "µg/m³",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # CO2 (Direct NDIR measurement: rco2)
        if data.get("rco2") is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "rco2",
                "timestamp": now,
                "measurement_type": MeasurementType.CO2,
                "value": float(data["rco2"]),
                "unit": "ppm",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # TVOC Index (Sensirion SGP41)
        if data.get("tvocIndex") is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "tvocIndex",
                "timestamp": now,
                "measurement_type": MeasurementType.VOC_INDEX,
                "value": float(data["tvocIndex"]),
                "unit": "index",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # NOx Index (Sensirion SGP41)
        if data.get("noxIndex") is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "noxIndex",
                "timestamp": now,
                "measurement_type": MeasurementType.NOX_INDEX,
                "value": float(data["noxIndex"]),
                "unit": "index",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # Temperature (atmpCompensated or atmp)
        temp = data.get("atmpCompensated") if data.get("atmpCompensated") is not None else data.get("atmp")
        if temp is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "atmp",
                "timestamp": now,
                "measurement_type": MeasurementType.TEMPERATURE,
                "value": float(temp),
                "unit": "°C",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        # Relative Humidity (rhumCompensated or rhum)
        hum = data.get("rhumCompensated") if data.get("rhumCompensated") is not None else data.get("rhum")
        if hum is not None:
            readings.append({
                "device_id": device_id,
                "sensor_id": "rhum",
                "timestamp": now,
                "measurement_type": MeasurementType.HUMIDITY,
                "value": float(hum),
                "unit": "%RH",
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "airgradient"
            })

        return readings

    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult:
        return CommandResult(
            success=False,
            message="AirGradient hardware monitors are read-only sensing stations without actuation controls.",
            command=command.command
        )

    async def health_check(self) -> AdapterHealth:
        connected = await self.test_connection()
        return AdapterHealth(
            is_connected=connected,
            status_message="AirGradient Local API accessible" if connected else "AirGradient monitor unreachable",
            last_communication=datetime.utcnow() if connected else None
        )

    async def disconnect(self) -> None:
        pass

