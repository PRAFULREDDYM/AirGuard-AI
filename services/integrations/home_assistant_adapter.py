import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from services.api.models import MeasurementType, DataProvenance, CalibrationQuality, IntegrationType
from services.integrations.base_adapter import (
    DeviceAdapter, DiscoveredDevice, AdapterHealth, DeviceCommand, CommandResult
)

class HomeAssistantAdapter:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> bool:
        """Calls GET /api/ to verify authentication and reachable instance."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/", headers=self.headers)
                return res.status_code == 200
        except Exception:
            return False

    async def discover(self) -> List[DiscoveredDevice]:
        """Discovers environmental sensors and controllable air purifiers from HA state inventory."""
        discovered = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{self.base_url}/api/states", headers=self.headers)
                if res.status_code != 200:
                    return []
                entities = res.json()

            for entity in entities:
                entity_id = entity.get("entity_id", "")
                attributes = entity.get("attributes", {})
                friendly_name = attributes.get("friendly_name", entity_id)

                if entity_id.startswith("sensor."):
                    device_class = attributes.get("device_class", "")
                    unit = attributes.get("unit_of_measurement", "")
                    m_type = self._map_device_class_to_type(device_class, entity_id)
                    if m_type:
                        discovered.append(DiscoveredDevice(
                            id=entity_id,
                            name=friendly_name,
                            manufacturer="Home Assistant Entity",
                            model=device_class or "Environmental Sensor",
                            protocol=IntegrationType.HOME_ASSISTANT,
                            is_controllable=False,
                            supported_measurements=[{"type": m_type.value, "unit": unit, "provenance": "MEASURED"}]
                        ))

                elif entity_id.startswith("fan."):
                    discovered.append(DiscoveredDevice(
                        id=entity_id,
                        name=friendly_name,
                        manufacturer="Home Assistant Controllable Fan",
                        model="Air Purifier / Ventilation Fan",
                        protocol=IntegrationType.HOME_ASSISTANT,
                        is_controllable=True,
                        supported_controls=[
                            {"command": "turn_on", "parameters": []},
                            {"command": "turn_off", "parameters": []},
                            {"command": "set_percentage", "parameters": ["percentage"]}
                        ]
                    ))
        except Exception:
            pass

        return discovered

    def _map_device_class_to_type(self, device_class: str, entity_id: str) -> Optional[MeasurementType]:
        dc = device_class.lower()
        eid = entity_id.lower()
        if dc == "pm25" or "pm25" in eid or "pm2_5" in eid:
            return MeasurementType.PM25
        elif dc == "pm10" or "pm10" in eid:
            return MeasurementType.PM10
        elif dc == "carbon_dioxide" or "co2" in eid:
            return MeasurementType.CO2
        elif dc in ["volatile_organic_compounds", "voc"] or "voc" in eid:
            return MeasurementType.VOC_INDEX
        elif dc == "temperature" or "temperature" in eid:
            return MeasurementType.TEMPERATURE
        elif dc == "humidity" or "humidity" in eid:
            return MeasurementType.HUMIDITY
        elif dc == "pressure" or "pressure" in eid:
            return MeasurementType.PRESSURE
        elif "nitrogen_dioxide" in dc or "nox" in eid:
            return MeasurementType.NOX_INDEX
        return None

    async def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        """Reads current state of a Home Assistant entity."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/states/{device_id}", headers=self.headers)
                if res.status_code != 200:
                    return []
                data = res.json()

            state = data.get("state")
            try:
                numeric_val = float(state)
            except (ValueError, TypeError):
                return []

            attributes = data.get("attributes", {})
            unit = attributes.get("unit_of_measurement", "")
            m_type = self._map_device_class_to_type(attributes.get("device_class", ""), device_id)
            if not m_type:
                return []

            return [{
                "device_id": device_id,
                "sensor_id": device_id,
                "timestamp": datetime.utcnow(),
                "measurement_type": m_type,
                "value": numeric_val,
                "unit": unit,
                "provenance": DataProvenance.MEASURED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "home_assistant"
            }]
        except Exception:
            return []

    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult:
        """Dispatches an actuation command to Home Assistant via service call."""
        domain = device_id.split(".")[0]
        cmd = command.command.lower()
        service = cmd

        payload = {"entity_id": device_id}

        if cmd == "set_speed":
            # Map speed string to percentage or preset mode
            speed = command.parameters.get("speed", "medium")
            pct = 100 if speed == "high" else (50 if speed == "medium" else 25)
            service = "set_percentage"
            payload["percentage"] = pct
        elif cmd == "set_percentage":
            service = "set_percentage"
            payload["percentage"] = command.parameters.get("percentage", 50)
        elif cmd in ["turn_on", "turn_off"]:
            service = cmd

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/services/{domain}/{service}",
                    headers=self.headers,
                    json=payload
                )
                if res.status_code in [200, 201]:
                    return CommandResult(
                        success=True,
                        message=f"HA service {domain}.{service} executed successfully on {device_id}.",
                        command=command.command
                    )
                else:
                    return CommandResult(
                        success=False,
                        message=f"HA returned status {res.status_code}: {res.text}",
                        command=command.command
                    )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to communicate with Home Assistant: {str(e)}",
                command=command.command
            )

    async def health_check(self) -> AdapterHealth:
        connected = await self.test_connection()
        return AdapterHealth(
            is_connected=connected,
            status_message="Connected to Home Assistant API" if connected else "Failed to connect to HA API",
            last_communication=datetime.utcnow() if connected else None
        )

    async def disconnect(self) -> None:
        pass

