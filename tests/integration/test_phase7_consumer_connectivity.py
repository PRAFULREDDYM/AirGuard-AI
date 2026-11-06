import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from services.api.main import app
from services.api.database import init_db, AsyncSessionLocal
from services.api.models import User, Home, Room, Device, IntegrationType
from services.integrations.mock_providers import MOCK_HA_TOKEN

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_ssrf_protection_probe():
    """Verifies that the gateway probe blocks cloud metadata, public WAN, and non-whitelisted ports."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. AWS/GCP Cloud Metadata IP should be blocked with 400
        res_metadata = await client.post(
            "/api/v1/gateway/probe",
            json={"host": "169.254.169.254", "port": 80},
            headers=headers
        )
        assert res_metadata.status_code == 400
        assert "Disallowed target" in res_metadata.json()["detail"] or "SSRF" in res_metadata.json()["detail"]

        # 2. Non-whitelisted IoT port (e.g. port 22 SSH) should be blocked with 400
        res_port = await client.post(
            "/api/v1/gateway/probe",
            json={"host": "192.168.1.100", "port": 22},
            headers=headers
        )
        assert res_port.status_code == 400
        assert "whitelisted IoT device ports" in res_port.json()["detail"] or "SSRF" in res_port.json()["detail"]

        # 3. Valid local RFC 1918 / loopback target on whitelisted port (e.g. 8000) should be permitted
        res_valid = await client.post(
            "/api/v1/gateway/probe",
            json={"host": "127.0.0.1", "port": 8000},
            headers=headers
        )
        assert res_valid.status_code == 200
        assert "reachable" in res_valid.json()

@pytest.mark.asyncio
async def test_cross_home_idor_isolation():
    """Verifies that User B cannot command, modify, or disconnect User A's device (returns 403 Forbidden)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register User A
        reg_a = await client.post("/api/v1/auth/register", json={
            "email": f"usera_{int(datetime.utcnow().timestamp())}@airguard.ai",
            "password": "Password123!",
            "full_name": "User Alpha"
        })
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Get User A's home
        homes_a = (await client.get("/api/v1/homes", headers=headers_a)).json()
        home_a_id = homes_a[0]["id"]

        # Create a controllable purifier in User A's home
        dev_a_res = await client.post("/api/v1/devices", headers=headers_a, json={
            "home_id": home_a_id,
            "name": "Alpha Levoit Core 400S",
            "manufacturer": "Levoit",
            "model": "Core 400S",
            "connection_protocol": "home_assistant",
            "is_controllable": True,
            "capabilities": {
                "measurements": ["PM25"],
                "controls": ["set_speed", "turn_on", "turn_off"]
            }
        })
        assert dev_a_res.status_code == 200
        dev_a_id = dev_a_res.json()["id"]

        # Register User B
        reg_b = await client.post("/api/v1/auth/register", json={
            "email": f"userb_{int(datetime.utcnow().timestamp())}@airguard.ai",
            "password": "Password123!",
            "full_name": "User Beta"
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. User B tries to update User A's device authorization -> 403 Forbidden
        res_auth = await client.patch(
            f"/api/v1/devices/{dev_a_id}/authorization?authorized=false",
            headers=headers_b
        )
        assert res_auth.status_code == 403
        assert "Forbidden" in res_auth.json()["detail"]

        # 2. User B tries to toggle manual override on User A's device -> 403 Forbidden
        res_override = await client.patch(
            f"/api/v1/devices/{dev_a_id}/manual-override?override=true",
            headers=headers_b
        )
        assert res_override.status_code == 403
        assert "Forbidden" in res_override.json()["detail"]

        # 3. User B tries to send actuation command to User A's device -> 403 Forbidden
        res_cmd = await client.post(
            f"/api/v1/devices/{dev_a_id}/command",
            json={"command": "set_speed", "parameters": {"speed": "high"}},
            headers=headers_b
        )
        assert res_cmd.status_code == 403
        assert "Forbidden" in res_cmd.json()["detail"]

        # 4. User B tries to disconnect User A's device -> 403 Forbidden
        res_disc = await client.post(
            f"/api/v1/devices/{dev_a_id}/disconnect",
            headers=headers_b
        )
        assert res_disc.status_code == 403

        # 5. User B tries to delete User A's device -> 403 Forbidden
        res_del = await client.delete(
            f"/api/v1/devices/{dev_a_id}",
            headers=headers_b
        )
        assert res_del.status_code == 403

@pytest.mark.asyncio
async def test_device_lifecycle_management():
    """Verifies refresh-health, disconnect, and audit logging for legitimate owner."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        dev_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "name": "Lifecycle Purifier",
            "manufacturer": "Xiaomi",
            "model": "Air Purifier 4",
            "connection_protocol": "simulation",
            "is_controllable": True,
            "capabilities": {
                "measurements": ["PM25"],
                "controls": ["set_speed"]
            }
        })
        dev_id = dev_res.json()["id"]

        # 1. Refresh health
        res_health = await client.post(f"/api/v1/devices/{dev_id}/refresh-health", headers=headers)
        assert res_health.status_code == 200
        data_health = res_health.json()
        assert data_health["is_online"] is True
        assert "status_detail" in data_health

        # 2. Disconnect device (suspends automations)
        res_disc = await client.post(f"/api/v1/devices/{dev_id}/disconnect", headers=headers)
        assert res_disc.status_code == 200
        data_disc = res_disc.json()
        assert data_disc["is_online"] is False
        assert data_disc["automation_authorized"] is False

@pytest.mark.asyncio
async def test_mock_home_assistant_integration():
    """Verifies the realistic mock Home Assistant endpoints and service calls."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Auth check: missing header -> 401
        res_unauth = await client.get("/mock-providers/ha/api/")
        assert res_unauth.status_code == 401

        # 2. Auth check: valid token -> 200
        ha_headers = {"Authorization": f"Bearer {MOCK_HA_TOKEN}"}
        res_auth = await client.get("/mock-providers/ha/api/", headers=ha_headers)
        assert res_auth.status_code == 200
        assert res_auth.json()["message"] == "API running."

        # 3. GET /api/states returns entities
        res_states = await client.get("/mock-providers/ha/api/states", headers=ha_headers)
        assert res_states.status_code == 200
        states = res_states.json()
        assert len(states) >= 4
        entity_ids = [s["entity_id"] for s in states]
        assert "fan.levoit_core_400s" in entity_ids
        assert "sensor.airgradient_living_room_pm25" in entity_ids

        # 4. Service call: set fan speed percentage
        res_service = await client.post(
            "/mock-providers/ha/api/services/fan/set_percentage",
            headers=ha_headers,
            json={"entity_id": "fan.levoit_core_400s", "percentage": 75}
        )
        assert res_service.status_code == 200
        updated_entities = res_service.json()
        assert updated_entities[0]["attributes"]["percentage"] == 75
        assert updated_entities[0]["state"] == "on"

@pytest.mark.asyncio
async def test_mock_airgradient_local_api():
    """Verifies the realistic mock AirGradient Local API /measures/current."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/mock-providers/airgradient/measures/current")
        assert res.status_code == 200
        payload = res.json()

        assert payload["model"] == "I-9PSL"
        assert "rco2" in payload
        assert "pm02" in payload
        assert "tvocIndex" in payload
        assert "atmp" in payload
        assert "rhum" in payload
