import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt

from services.api.models import MeasurementType, DataProvenance, CalibrationQuality, IntegrationType
from services.integrations.base_adapter import (
    DeviceAdapter, DiscoveredDevice, AdapterHealth, DeviceCommand, CommandResult
)

logger = logging.getLogger(__name__)

class MQTTAdapter:
    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.telemetry_callback = telemetry_callback

        self.client: Optional[mqtt.Client] = None
        self.is_connected: bool = False
        self.discovered_devices: Dict[str, DiscoveredDevice] = {}
        self.latest_payloads: Dict[str, Dict[str, Any]] = {}

    def _setup_client(self):
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to HA discovery topics and custom telemetry topics
            client.subscribe("homeassistant/sensor/#", qos=1)
            client.subscribe("airguard/#", qos=1)
            client.subscribe("sensors/#", qos=1)
        else:
            self.is_connected = False
            logger.error(f"MQTT connection failed with reason code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload_str = msg.payload.decode("utf-8")
        except Exception:
            return

        # Handle Home Assistant MQTT Discovery
        if topic.startswith("homeassistant/sensor/") and topic.endswith("/config"):
            self._parse_ha_discovery(topic, payload_str)
            return

        # Handle telemetry payloads (JSON or raw values)
        try:
            data = json.loads(payload_str)
        except Exception:
            try:
                data = {"value": float(payload_str)}
            except ValueError:
                data = {"raw": payload_str}

        self.latest_payloads[topic] = {
            "timestamp": datetime.utcnow(),
            "data": data
        }

        if self.telemetry_callback:
            self.telemetry_callback({"topic": topic, "payload": data})

    def _parse_ha_discovery(self, topic: str, config_json: str):
        try:
            cfg = json.loads(config_json)
            dev_info = cfg.get("device", {})
            dev_id = cfg.get("unique_id") or topic.split("/")[-2]
            name = cfg.get("name") or dev_info.get("name", dev_id)
            device_class = cfg.get("device_class", "")
            unit = cfg.get("unit_of_measurement", "")

            discovered = DiscoveredDevice(
                id=f"mqtt_{dev_id}",
                name=name,
                manufacturer=dev_info.get("manufacturer", "MQTT Device"),
                model=dev_info.get("model", "ESP32 / ESPHome"),
                firmware_version=dev_info.get("sw_version", "1.0.0"),
                protocol=IntegrationType.MQTT,
                is_controllable=bool(cfg.get("command_topic")),
                supported_measurements=[{"type": device_class.upper(), "unit": unit, "provenance": "MEASURED"}]
            )
            self.discovered_devices[dev_id] = discovered
        except Exception as e:
            logger.error(f"Error parsing MQTT discovery payload: {e}")

    async def test_connection(self) -> bool:
        if not self.client:
            self._setup_client()
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=10)
            self.client.loop_start()
            # Wait up to 2 seconds for on_connect
            import asyncio
            for _ in range(20):
                if self.is_connected:
                    return True
                await asyncio.sleep(0.1)
            return self.is_connected
        except Exception:
            return False

    async def discover(self) -> List[DiscoveredDevice]:
        return list(self.discovered_devices.values())

    async def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        # Fetch latest cached readings
        readings = []
        now = datetime.utcnow()
        for topic, item in list(self.latest_payloads.items()):
            data = item["data"]
            if isinstance(data, dict) and "pm25" in data:
                readings.append({
                    "device_id": device_id,
                    "sensor_id": f"{topic}_pm25",
                    "timestamp": now,
                    "measurement_type": MeasurementType.PM25,
                    "value": float(data["pm25"]),
                    "unit": "µg/m³",
                    "provenance": DataProvenance.MEASURED,
                    "calibration_quality": CalibrationQuality.CALIBRATED,
                    "source_integration": "mqtt"
                })
        return readings

    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult:
        if not self.is_connected or not self.client:
            return CommandResult(success=False, message="MQTT broker not connected.", command=command.command)

        topic = f"airguard/{device_id}/set"
        payload = json.dumps({"command": command.command, "params": command.parameters})
        info = self.client.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=3.0)
        return CommandResult(
            success=True,
            message=f"Command published to topic '{topic}'.",
            command=command.command
        )

    async def health_check(self) -> AdapterHealth:
        return AdapterHealth(
            is_connected=self.is_connected,
            status_message=f"MQTT connected to {self.broker_host}" if self.is_connected else "MQTT disconnected",
            last_communication=datetime.utcnow() if self.is_connected else None
        )

    async def disconnect(self) -> None:
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False

