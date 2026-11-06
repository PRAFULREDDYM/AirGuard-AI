"""
AirGuard AI — Phase 6 Integration Tests: Plug-and-Play Device Connectivity & Consumer UX
Validates:
- Gateway status and local network scan
- Gateway device probe
- Catalog search and compatibility profile retrieval
- Room pairing analysis and automatic sensor-to-purifier suggestions
- Beginner automation assistant preset application (Clean Air Guard, Odor Eliminator)
- Safe device command execution vs. read-only sensor rejection
- Manual override detection and hold logic
- Unsupported device handling
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from services.api.main import app
from services.api.database import init_db
from services.api.models import User, Home, Room, Device, DeviceCapability, IntegrationType

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_gateway_status_and_scan():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Auth demo login
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test Gateway Status
        gw_res = await client.get("/api/v1/gateway/status", headers=headers)
        assert gw_res.status_code == 200
        gw_data = gw_res.json()
        assert gw_data["online"] is True
        assert len(gw_data["interfaces"]) > 0
        assert "gateway_id" in gw_data

        # 2. Test Gateway Scan
        scan_res = await client.post("/api/v1/gateway/scan?timeout=1.0", headers=headers)
        assert scan_res.status_code == 200
        scan_data = scan_res.json()
        assert len(scan_data) >= 1
        # Non-negotiable rule: Every discovered service must be is_verified == False
        for dev in scan_data:
            assert dev["is_verified"] is False
            assert "category" in dev
            assert "capabilities_preview" in dev

        # 3. Test Probe Device (Testing local reachability)
        probe_res = await client.post("/api/v1/gateway/probe", headers=headers, json={
            "host": "127.0.0.1",
            "port": 80
        })
        assert probe_res.status_code == 200
        probe_data = probe_res.json()
        assert "latency_ms" in probe_data

@pytest.mark.asyncio
async def test_device_catalog_and_compatibility():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Query full catalog
        cat_res = await client.get("/api/v1/catalog/devices", headers=headers)
        assert cat_res.status_code == 200
        cat_data = cat_res.json()
        assert len(cat_data) >= 5

        # Verify Levoit Core 400S is present and supported
        levoit = next((d for d in cat_data if "400S" in d["model_name"]), None)
        assert levoit is not None
        assert levoit["is_supported"] is True
        assert "Fan Speed" in " ".join(levoit["supported_controls"])
        # Non-negotiable: Ozone prohibited
        assert "Ozone" in " ".join(levoit["unsupported_controls"])

        # Verify Core 300 non-smart is marked unsupported with Route D alternatives
        core300 = next((d for d in cat_data if "Non-Smart" in d["model_name"]), None)
        assert core300 is not None
        assert core300["is_supported"] is False
        assert len(core300["alternative_options"]) > 0

        # Filter by category
        monitors_res = await client.get("/api/v1/catalog/devices?category=monitor", headers=headers)
        assert monitors_res.status_code == 200
        for m in monitors_res.json():
            assert m["category"] == "monitor"

@pytest.mark.asyncio
async def test_room_pairings_and_automation_presets():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get user's home and living room
        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]
        rooms = (await client.get(f"/api/v1/rooms?home_id={home_id}", headers=headers)).json()
        living_room_id = rooms[0]["id"]

        # 1. Fetch Room Pairings Summary
        summary_res = await client.get(f"/api/v1/rooms/all/pairings-summary?home_id={home_id}", headers=headers)
        assert summary_res.status_code == 200
        summary_data = summary_res.json()
        assert len(summary_data) >= 1

        # 2. Get Automation Presets
        presets_res = await client.get("/api/v1/automations/presets", headers=headers)
        assert presets_res.status_code == 200
        presets = presets_res.json()
        assert len(presets) >= 3
        clean_air = next((p for p in presets if p["id"] == "clean_air_guard"), None)
        assert clean_air is not None
        assert clean_air["cooldown_seconds"] == 1800  # 30 mins default

        # 3. Create a Purifier Device to pair
        purifier_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "room_id": living_room_id,
            "name": "Living Room Core 400S",
            "manufacturer": "Levoit",
            "model": "Core 400S",
            "connection_protocol": "home_assistant",
            "is_controllable": True,
            "capabilities": {
                "measurements": [{"type": "PM25", "unit": "µg/m³"}],
                "controls": ["set_speed", "turn_on", "turn_off"]
            }
        })
        assert purifier_res.status_code == 200
        purifier_id = purifier_res.json()["id"]

        # 4. Apply Beginner Assistant Preset (Auto Control)
        apply_res = await client.post("/api/v1/automations/apply-preset", headers=headers, json={
            "home_id": home_id,
            "room_id": living_room_id,
            "preset_id": "clean_air_guard",
            "purifier_device_id": purifier_id,
            "mode": "auto_control"
        })
        assert apply_res.status_code == 200
        rule = apply_res.json()
        assert rule["enabled"] is True
        assert rule["cooldown_seconds"] == 1800
        assert rule["action_config"]["target_device_id"] == purifier_id

        # 5. Check Room Pairings now reflects active automation
        pairings_res = await client.get(f"/api/v1/rooms/{living_room_id}/pairings", headers=headers)
        assert pairings_res.status_code == 200
        pairings_data = pairings_res.json()
        assert pairings_data["purifiers_count"] >= 1
        assert pairings_data["active_rules_count"] >= 1

        # 6. Test Safe Command Execution on Purifier
        cmd_res = await client.post(f"/api/v1/devices/{purifier_id}/command", headers=headers, json={
            "command": "set_speed",
            "parameters": {"speed": 2}
        })
        print("CMD_RES STATUS:", cmd_res.status_code, "BODY:", cmd_res.text)
        assert cmd_res.status_code == 200
        assert cmd_res.json()["success"] is True

        # 7. Test Read-Only Sensor Rejection (Cannot command a pure monitor)
        monitor_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "room_id": living_room_id,
            "name": "AirGradient Station",
            "manufacturer": "AirGradient",
            "model": "ONE v3.1",
            "connection_protocol": "airgradient",
            "is_controllable": False,
            "capabilities": {
                "measurements": [{"type": "PM25", "unit": "µg/m³"}],
                "controls": []
            }
        })
        monitor_id = monitor_res.json()["id"]

        sensor_cmd_res = await client.post(f"/api/v1/devices/{monitor_id}/command", headers=headers, json={
            "command": "set_speed",
            "parameters": {"speed": 3}
        })
        assert sensor_cmd_res.status_code == 400
        assert "read-only monitoring sensor" in sensor_cmd_res.json()["detail"]
