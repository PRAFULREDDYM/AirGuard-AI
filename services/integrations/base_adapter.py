from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from services.api.models import MeasurementType, DataProvenance, CalibrationQuality, IntegrationType

class DiscoveredDevice(BaseModel):
    id: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    protocol: IntegrationType
    is_controllable: bool = False
    supported_measurements: List[Dict[str, Any]] = []
    supported_controls: List[Dict[str, Any]] = []

class AdapterHealth(BaseModel):
    is_connected: bool
    status_message: str
    last_communication: Optional[datetime] = None

class DeviceCommand(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}

class CommandResult(BaseModel):
    success: bool
    message: str
    command: str
    timestamp: datetime = datetime.utcnow()

class DeviceAdapter(Protocol):
    async def discover(self) -> List[DiscoveredDevice]:
        ...
    async def test_connection(self) -> bool:
        ...
    async def read_telemetry(self, device_id: str) -> List[Dict[str, Any]]:
        ...
    async def send_command(self, device_id: str, command: DeviceCommand) -> CommandResult:
        ...
    async def health_check(self) -> AdapterHealth:
        ...
    async def disconnect(self) -> None:
        ...

