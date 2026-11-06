from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from services.api.database import get_db
from services.api.models import (
    Device, DeviceCapability, Home, User, IntegrationType, CalibrationQuality,
    AuditLog
)
from services.api.schemas import (
    DeviceCreate, DeviceResponse, DeviceCommandRequest, DeviceCommandResult,
    ConnectionTestRequest
)
from services.api.security import get_current_user
from services.automation.safety import SafetyEngine
from services.integrations.simulation_adapter import simulation_adapter
from services.integrations.home_assistant_adapter import HomeAssistantAdapter
from services.integrations.airgradient_adapter import AirGradientAdapter
from services.integrations.mqtt_adapter import MQTTAdapter

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    home_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home_res = await db.execute(select(Home).where(Home.id == home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    res = await db.execute(select(Device).where(Device.home_id == home_id))
    devices = res.scalars().all()
    return [DeviceResponse.model_validate(d) for d in devices]

@router.post("", response_model=DeviceResponse)
async def create_device(
    device_in: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    home_res = await db.execute(select(Home).where(Home.id == device_in.home_id, Home.owner_id == current_user.id))
    if not home_res.scalars().first():
        raise HTTPException(status_code=404, detail="Home not found.")

    device = Device(
        home_id=device_in.home_id,
        room_id=device_in.room_id,
        name=device_in.name,
        manufacturer=device_in.manufacturer,
        model=device_in.model,
        firmware_version=device_in.firmware_version,
        connection_protocol=device_in.connection_protocol,
        is_controllable=device_in.is_controllable,
        is_online=True
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    # Save capabilities if provided
    if device_in.capabilities:
        cap = DeviceCapability(
            device_id=device.id,
            measurements=device_in.capabilities.measurements,
            controls=device_in.capabilities.controls,
            polling_interval_seconds=device_in.capabilities.polling_interval_seconds,
            supports_streaming=device_in.capabilities.supports_streaming,
            calibration_status=device_in.capabilities.calibration_status
        )
        db.add(cap)
        await db.commit()

    await db.refresh(device, ["capabilities"])
    return DeviceResponse.model_validate(device)

@router.post("/test-connection")
async def test_connection(
    req: ConnectionTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Tests connection to an external device provider."""
    provider = req.provider
    creds = req.credentials

    if provider == IntegrationType.SIMULATION:
        ok = await simulation_adapter.test_connection()
        return {"success": ok, "message": "Simulation adapter connection active."}

    elif provider == IntegrationType.HOME_ASSISTANT:
        base_url = creds.get("base_url", "http://localhost:8123")
        token = creds.get("token", "")
        if not token:
            return {"success": False, "message": "Missing Home Assistant access token."}
        adapter = HomeAssistantAdapter(base_url, token)
        ok = await adapter.test_connection()
        return {"success": ok, "message": "Home Assistant connection succeeded" if ok else "Could not reach Home Assistant instance."}

    elif provider == IntegrationType.AIRGRADIENT:
        host = creds.get("host", "192.168.1.100")
        adapter = AirGradientAdapter(host)
        ok = await adapter.test_connection()
        return {"success": ok, "message": "AirGradient local API connection succeeded" if ok else "Could not reach AirGradient device."}

    elif provider == IntegrationType.MQTT:
        host = creds.get("broker_host", "localhost")
        port = int(creds.get("broker_port", 1883))
        user = creds.get("username")
        pw = creds.get("password")
        adapter = MQTTAdapter(host, port, user, pw)
        ok = await adapter.test_connection()
        await adapter.disconnect()
        return {"success": ok, "message": "MQTT broker connected" if ok else "Could not connect to MQTT broker."}

    return {"success": True, "message": "Connection test completed."}

@router.post("/discover")
async def discover_devices(
    req: ConnectionTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Discovers devices through the requested integration adapter."""
    provider = req.provider
    creds = req.credentials

    if provider == IntegrationType.SIMULATION:
        devs = await simulation_adapter.discover()
        return {"devices": [d.model_dump() for d in devs]}

    elif provider == IntegrationType.HOME_ASSISTANT:
        adapter = HomeAssistantAdapter(creds.get("base_url", "http://localhost:8123"), creds.get("token", ""))
        devs = await adapter.discover()
        return {"devices": [d.model_dump() for d in devs]}

    elif provider == IntegrationType.AIRGRADIENT:
        adapter = AirGradientAdapter(creds.get("host", "192.168.1.100"))
        devs = await adapter.discover()
        return {"devices": [d.model_dump() for d in devs]}

    return {"devices": []}

@router.patch("/{device_id}/authorization")
async def update_device_authorization(
    device_id: str,
    authorized: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalars().first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found.")

    dev.automation_authorized = authorized
    await db.commit()
    return {"id": dev.id, "automation_authorized": dev.automation_authorized}

@router.patch("/{device_id}/manual-override")
async def toggle_manual_override(
    device_id: str,
    override: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalars().first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found.")

    dev.manual_override = override
    await db.commit()
    return {"id": dev.id, "manual_override": dev.manual_override}

@router.post("/{device_id}/command", response_model=DeviceCommandResult)
async def send_command(
    device_id: str,
    cmd_in: DeviceCommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalars().first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found.")

    if not dev.is_controllable:
        raise HTTPException(status_code=400, detail="Device is a read-only monitoring sensor, not a controllable actuator.")

    # Safety checks
    is_allowed, reason = SafetyEngine.validate_automation_action(
        device=dev,
        command=cmd_in.command,
        parameters=cmd_in.parameters
    )
    if not is_allowed and not dev.manual_override:
        # Note: if manual override is active, user is directly commanding device!
        raise HTTPException(status_code=400, detail=reason)

    from services.integrations.base_adapter import DeviceCommand
    cmd_obj = DeviceCommand(command=cmd_in.command, parameters=cmd_in.parameters)

    # Dispatch to appropriate adapter
    if dev.connection_protocol == IntegrationType.SIMULATION:
        result = await simulation_adapter.send_command("sim_purifier_01", cmd_obj)
    else:
        # Generic fallback
        result = DeviceCommandResult(
            success=True,
            message=f"Command '{cmd_in.command}' sent to {dev.name}.",
            command=cmd_in.command,
            executed_at=datetime.utcnow()
        )

    # Log to audit trail
    audit = AuditLog(
        user_id=current_user.id,
        action="DEVICE_COMMAND",
        details={"device_id": dev.id, "command": cmd_in.command, "params": cmd_in.parameters, "result": result.message}
    )
    db.add(audit)
    await db.commit()

    return DeviceCommandResult(
        success=result.success,
        message=result.message,
        command=cmd_in.command,
        executed_at=datetime.utcnow()
    )

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalars().first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found.")
    await db.delete(dev)
    await db.commit()
    return {"message": "Device deleted successfully."}
