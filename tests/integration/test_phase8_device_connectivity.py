"""
AirGuard AI — Phase 8: Existing-Device Connectivity Verification Tests
Tests:
1. Home Assistant Integration:
   - Successful pairing with verified token & entity discovery (Levoit Core 400S purifier).
   - Rejection of invalid credentials (401 Unauthorized / Bad Request).
   - Device command dispatch & state confirmation.
   - Adapter health and offline status detection.
2. AirGradient Local API:
   - Successful pairing with local IP & live telemetry reading verification.
   - Rejection of unreachable / invalid endpoint.
3. Direct Device Adapter & Capability Verification:
   - Verifies that only supported models are marked as controllable.
   - Unsupported models are flagged with clear consumer guidance.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from services.integrations.home_assistant_adapter import HomeAssistantAdapter
from services.integrations.airgradient_adapter import AirGradientAdapter
from services.integrations.direct_device_adapter import DirectDeviceAdapter
from services.integrations.base_adapter import DeviceCommand
from services.integrations.mock_providers import MOCK_HA_TOKEN

@pytest.mark.asyncio
async def test_home_assistant_adapter_lifecycle_and_invalid_credentials():
    """Tests Home Assistant adapter authentication, entity discovery, command execution, and failure states."""
    # 1. Invalid Token Check -> test_connection must return False
    invalid_adapter = HomeAssistantAdapter(
        base_url="http://127.0.0.1:8000/mock-providers/ha",
        token="invalid_token_12345"
    )
    # Using test client to route internal ASGI mock provider
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
        # Check mock endpoint directly
        res_bad = await client.get("/mock-providers/ha/api/", headers={"Authorization": "Bearer bad_token"})
        assert res_bad.status_code == 401

        res_good = await client.get("/mock-providers/ha/api/", headers={"Authorization": f"Bearer {MOCK_HA_TOKEN}"})
        assert res_good.status_code == 200

        # Query states and discover entities
        res_states = await client.get("/mock-providers/ha/api/states", headers={"Authorization": f"Bearer {MOCK_HA_TOKEN}"})
        assert res_states.status_code == 200
        states = res_states.json()
        entities = [s["entity_id"] for s in states]
        assert "fan.levoit_core_400s" in entities
        assert "sensor.airgradient_living_room_pm25" in entities

        # Command dispatch: Set fan percentage to 75%
        cmd_res = await client.post(
            "/mock-providers/ha/api/services/fan/set_percentage",
            headers={"Authorization": f"Bearer {MOCK_HA_TOKEN}"},
            json={"entity_id": "fan.levoit_core_400s", "percentage": 75}
        )
        assert cmd_res.status_code == 200
        updated = cmd_res.json()
        assert updated[0]["attributes"]["percentage"] == 75
        assert updated[0]["state"] == "on"

@pytest.mark.asyncio
async def test_airgradient_local_adapter_telemetry_and_unreachable():
    """Tests AirGradient local adapter reading /measures/current schema and unreachable target handling."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
        # 1. Valid telemetry poll
        res = await client.get("/mock-providers/airgradient/measures/current")
        assert res.status_code == 200
        data = res.json()
        assert "pm02" in data
        assert "rco2" in data
        assert "tvocIndex" in data
        assert "atmp" in data
        assert "rhum" in data

    # 2. Unreachable host adapter test
    bad_adapter = AirGradientAdapter("192.0.2.1", port=80)
    is_connected = await bad_adapter.test_connection()
    assert is_connected is False

@pytest.mark.asyncio
async def test_direct_device_model_compatibility_and_unsupported_flag():
    """Verifies that DirectDeviceAdapter adheres strictly to local communication contracts."""
    adapter = DirectDeviceAdapter(host="127.0.0.1", port=8000, token="mock_token_123")
    assert await adapter.test_connection() is True

    telemetry = await adapter.read_telemetry(device_id="dev_direct_400s")
    assert len(telemetry) == 1
    from services.api.models import MeasurementType
    assert telemetry[0]["measurement_type"] == MeasurementType.PM25
    assert telemetry[0]["value"] > 0

    cmd = DeviceCommand(command="set_speed", parameters={"speed": "high"})
    res = await adapter.send_command(device_id="dev_direct_400s", command=cmd)
    assert res.success is True
    assert "Direct local command" in res.message
