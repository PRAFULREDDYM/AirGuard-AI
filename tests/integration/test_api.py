import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from services.api.main import app
from services.api.database import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_full_user_and_device_vertical_slice():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register new user
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": f"test_{int(datetime.utcnow().timestamp())}@airguard.ai",
            "password": "Password123!",
            "full_name": "Test Engineer"
        })
        assert reg_res.status_code == 200
        token_data = reg_res.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get me
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        user_id = me_res.json()["id"]

        # 3. List homes (auto-created default home)
        homes_res = await client.get("/api/v1/homes", headers=headers)
        assert homes_res.status_code == 200
        homes = homes_res.json()
        assert len(homes) >= 1
        home_id = homes[0]["id"]

        # 4. List rooms (auto-created default living room)
        rooms_res = await client.get(f"/api/v1/rooms?home_id={home_id}", headers=headers)
        assert rooms_res.status_code == 200
        rooms = rooms_res.json()
        assert len(rooms) >= 1
        room_id = rooms[0]["id"]

        # 5. Create a Controllable Purifier Device
        dev_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "name": "Integration Test Purifier",
            "manufacturer": "AirGuard SafePurifier",
            "model": "Test-400",
            "connection_protocol": "simulation",
            "is_controllable": True,
            "capabilities": {
                "measurements": [{"type": "PM25", "unit": "µg/m³"}],
                "controls": [{"command": "set_speed", "parameters": ["low", "high"]}]
            }
        })
        assert dev_res.status_code == 200
        purifier_id = dev_res.json()["id"]

        # Authorize automation on purifier
        auth_res = await client.patch(f"/api/v1/devices/{purifier_id}/authorization?authorized=true", headers=headers)
        assert auth_res.status_code == 200
        assert auth_res.json()["automation_authorized"] is True

        # 6. Create Automation Rule: PM2.5 > 35 -> set_speed high
        rule_res = await client.post("/api/v1/automations", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "name": "Auto High Purifier on Smoke",
            "enabled": True,
            "trigger_config": {
                "measurement_type": "PM25",
                "condition": "ABOVE",
                "threshold": 35.0,
                "duration_seconds": 60
            },
            "action_config": {
                "device_id": purifier_id,
                "command": "set_speed",
                "parameters": {"speed": "high"}
            },
            "cooldown_seconds": 60,
            "max_executions_per_hour": 10
        })
        assert rule_res.status_code == 200
        rule_id = rule_res.json()["id"]

        # 7. Ingest elevated PM2.5 reading (e.g. 58.0 µg/m³)
        reading_res = await client.post("/api/v1/readings", headers=headers, json={
            "device_id": purifier_id,
            "sensor_id": "test_pm25_sensor",
            "timestamp": datetime.utcnow().isoformat(),
            "measurement_type": "PM25",
            "value": 58.0,
            "unit": "µg/m³",
            "provenance": "SIMULATED",
            "calibration_quality": "CALIBRATED",
            "source_integration": "simulation"
        })
        assert reading_res.status_code == 200
        assert reading_res.json()["value"] == 58.0

        # 8. Verify Event was created due to threshold limit
        events_res = await client.get(f"/api/v1/events?room_id={room_id}", headers=headers)
        assert events_res.status_code == 200
        events = events_res.json()
        assert len(events) >= 1
        assert "High PM25 Level" in events[0]["title"]

        # 9. Verify Automation was executed
        execs_res = await client.get(f"/api/v1/automations/executions?rule_id={rule_id}", headers=headers)
        assert execs_res.status_code == 200
        execs = execs_res.json()
        assert len(execs) >= 1
        assert execs[0]["status"] == "SUCCESS"
        assert execs[0]["command"] == "set_speed"

        # 10. Test Molecular Odor Prediction endpoint
        mol_res = await client.post("/api/v1/models/molecular/predict", json={
            "smiles": "CC(=O)OCCC(C)C"  # Isoamyl acetate (banana)
        })
        assert mol_res.status_code == 200
        mol_data = mol_res.json()
        assert mol_data["is_valid_smiles"] is True
        assert len(mol_data["predicted_descriptors"]) > 0

@pytest.mark.asyncio
async def test_demo_login_production_guard():
    from services.api.config import settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # In development/test mode, demo-login succeeds
        original_env = settings.ENVIRONMENT
        try:
            settings.ENVIRONMENT = "development"
            dev_res = await client.post("/api/v1/auth/demo-login")
            assert dev_res.status_code == 200
            assert "access_token" in dev_res.json()

            # In production mode, demo-login must be blocked with 403 Forbidden
            settings.ENVIRONMENT = "production"
            prod_res = await client.post("/api/v1/auth/demo-login")
            assert prod_res.status_code == 403
            assert "disabled in production" in prod_res.json()["detail"]
        finally:
            settings.ENVIRONMENT = original_env

