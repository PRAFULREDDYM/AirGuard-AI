import asyncio
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from services.api.models import MeasurementType, DataProvenance, CalibrationQuality, IntegrationType
from services.integrations.base_adapter import (
    DeviceAdapter, DiscoveredDevice, AdapterHealth, DeviceCommand, CommandResult
)

class SimulationAdapter:
    def __init__(self):
        self.scenario: str = "normal"  # normal, cooking, cleaning
        self.purifier_state: Dict[str, Any] = {
            "power": "on",
            "speed": "medium",
            "percentage": 50
        }
        self.last_tick: datetime = datetime.utcnow()

    def set_scenario(self, scenario: str):
        self.scenario = scenario

    async def discover(self) -> List[DiscoveredDevice]:
        return [
            DiscoveredDevice(
                id="sim_airgradient_01",
                name="Simulated AirGradient ONE",
                manufacturer="AirGradient (Simulated)",
                model="ONE v3.1",
                firmware_version="3.1.4",
                protocol=IntegrationType.SIMULATION,
                is_controllable=False,
                supported_measurements=[
                    {"type": "PM25", "unit": "µg/m³", "provenance": "SIMULATED"},
                    {"type": "PM10", "unit": "µg/m³", "provenance": "SIMULATED"},
                    {"type": "CO2", "unit": "ppm", "provenance": "SIMULATED"},
                    {"type": "VOC_INDEX", "unit": "index", "provenance": "SIMULATED"},
                    {"type": "NOX_INDEX", "unit": "index", "provenance": "SIMULATED"},
                    {"type": "TEMPERATURE", "unit": "°C", "provenance": "SIMULATED"},
                    {"type": "HUMIDITY", "unit": "%RH", "provenance": "SIMULATED"},
                ],
                supported_controls=[]
            ),
            DiscoveredDevice(
                id="sim_purifier_01",
                name="Simulated Smart HEPA Purifier",
                manufacturer="AirGuard SafePurifier (Simulated)",
                model="CleanAir Pro-400",
                firmware_version="1.2.0",
                protocol=IntegrationType.SIMULATION,
                is_controllable=True,
                supported_measurements=[
                    {"type": "PM25", "unit": "µg/m³", "provenance": "SIMULATED"}
                ],
                supported_controls=[
                    {"command": "set_speed", "parameters": ["low", "medium", "high", "auto"]},
                    {"command": "turn_on", "parameters": []},
                    {"command": "turn_off", "parameters": []}
                ]
            )
        ]

    async def test_connection(self) -> bool:
        return True

    async def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        readings = []

        if device_id == "sim_airgradient_01":
            # Baseline ranges
            pm25 = random.uniform(8.0, 14.0)
            pm10 = pm25 * random.uniform(1.2, 1.6)
            co2 = random.uniform(480.0, 620.0)
            voc = random.uniform(80.0, 120.0)
            nox = random.uniform(1.0, 5.0)
            temp = random.uniform(21.5, 23.0)
            hum = random.uniform(42.0, 48.0)

            # Scenario modifications
            if self.scenario == "cooking":
                pm25 = random.uniform(45.0, 78.0)
                pm10 = pm25 * 1.5
                voc = random.uniform(220.0, 310.0)
                temp = random.uniform(23.5, 25.0)
            elif self.scenario == "cleaning":
                voc = random.uniform(320.0, 440.0)
                pm25 = random.uniform(10.0, 18.0)
            elif self.purifier_state.get("speed") == "high":
                # High purifier active drops particles quickly
                pm25 = max(4.0, pm25 * 0.4)
                pm10 = max(6.0, pm10 * 0.4)

            readings.extend([
                {
                    "device_id": device_id,
                    "sensor_id": "sim_pm25",
                    "timestamp": now,
                    "measurement_type": MeasurementType.PM25,
                    "value": round(pm25, 2),
                    "unit": "µg/m³",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_pm10",
                    "timestamp": now,
                    "measurement_type": MeasurementType.PM10,
                    "value": round(pm10, 2),
                    "unit": "µg/m³",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_co2",
                    "timestamp": now,
                    "measurement_type": MeasurementType.CO2,
                    "value": round(co2, 1),
                    "unit": "ppm",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_voc",
                    "timestamp": now,
                    "measurement_type": MeasurementType.VOC_INDEX,
                    "value": round(voc, 1),
                    "unit": "index",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_nox",
                    "timestamp": now,
                    "measurement_type": MeasurementType.NOX_INDEX,
                    "value": round(nox, 1),
                    "unit": "index",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_temp",
                    "timestamp": now,
                    "measurement_type": MeasurementType.TEMPERATURE,
                    "value": round(temp, 1),
                    "unit": "°C",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                },
                {
                    "device_id": device_id,
                    "sensor_id": "sim_hum",
                    "timestamp": now,
                    "measurement_type": MeasurementType.HUMIDITY,
                    "value": round(hum, 1),
                    "unit": "%RH",
                    "provenance": DataProvenance.SIMULATED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "simulation"
                }
            ])
            self.last_tick = now

        elif device_id == "sim_purifier_01":
            # Outlet PM2.5 sensor on purifier
            purifier_pm = 3.0 if self.purifier_state.get("power") == "on" else 15.0
            readings.append({
                "device_id": device_id,
                "sensor_id": "purifier_outlet_pm25",
                "timestamp": now,
                "measurement_type": MeasurementType.PM25,
                "value": round(purifier_pm, 1),
                "unit": "µg/m³",
                "provenance": DataProvenance.SIMULATED,
                "calibration_quality": CalibrationQuality.CALIBRATED,
                "source_integration": "simulation"
            })

        return readings

    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult:
        if device_id != "sim_purifier_01":
            return CommandResult(
                success=False,
                message=f"Device '{device_id}' does not support actuation commands.",
                command=command.command
            )

        cmd = command.command.lower()
        if cmd == "set_speed":
            speed = command.parameters.get("speed", "medium")
            self.purifier_state["speed"] = speed
            self.purifier_state["power"] = "on"
            return CommandResult(
                success=True,
                message=f"Purifier fan speed adjusted to '{speed}'.",
                command=command.command
            )
        elif cmd == "turn_on":
            self.purifier_state["power"] = "on"
            return CommandResult(success=True, message="Purifier powered on.", command=command.command)
        elif cmd == "turn_off":
            self.purifier_state["power"] = "off"
            return CommandResult(success=True, message="Purifier powered off.", command=command.command)

        return CommandResult(
            success=False,
            message=f"Unknown command '{command.command}'.",
            command=command.command
        )

    async def health_check(self) -> AdapterHealth:
        return AdapterHealth(
            is_connected=True,
            status_message="Simulation engine operational (synthetic labeled stream)",
            last_communication=datetime.utcnow()
        )

    async def disconnect(self) -> None:
        pass

simulation_adapter = SimulationAdapter()

