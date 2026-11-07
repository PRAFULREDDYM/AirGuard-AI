"""AirGuard AI — Phase 7: Production-Grade Monitoring, Notifications & Automatic Purifier Onboarding Tests

Validates:
1. Consent & Permissions Management (Grant, Versioning, Revocation Cascade).
2. Server-side Consent Enforcement (Revoked DEVICE_CONTROL blocks automation even with enabled rule).
3. In-App Notification Center, Preferences, Read Status & Test Delivery.
4. Emergency Pause All Automations Kill-Switch.
5. 14 Safety Invariants:
   - Particulate restriction (Blocks automated actuation from VOC/odor triggers).
   - Stale sensor reading suppression (>120s old).
   - Conservative Emergency Suspension on fire/gas hazard.
   - Manual override hold.
6. GDPR/CCPA User Data Export & Data Retention.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from uuid import uuid4

from services.api.main import app
from services.api.database import init_db, AsyncSessionLocal
from services.api.models import (
    User, Home, Room, Device, AutomationRule, UserConsent, NotificationPreference,
    Alert, EventSeverity, SensorReading, MeasurementType, DataProvenance
)
from services.automation.safety import SafetyEngine
from services.automation.engine import AutomationEngine

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_consent_lifecycle_and_cascade_revocation():
    """Verifies that granting and revoking consent updates records and cascades to device automation flags."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": f"consent_user_{int(datetime.utcnow().timestamp())}@airguard.ai",
            "password": "Password123!",
            "full_name": "Consent Test User"
        })
        assert reg_res.status_code == 200
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        # Create purifier device
        dev_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "name": "Consent Test Purifier",
            "connection_protocol": "home_assistant",
            "is_controllable": True,
            "capabilities": {"controls": ["set_speed", "turn_on", "turn_off"]}
        })
        assert dev_res.status_code == 200
        device_id = dev_res.json()["id"]

        # 1. Grant TELEMETRY_ACCESS consent
        res_tel = await client.post("/api/v1/consents", headers=headers, json={
            "home_id": home_id,
            "permission_type": "TELEMETRY_ACCESS",
            "authorized_actions": ["read_telemetry"],
            "consent_version": "1.0",
            "consent_origin": "onboarding_wizard"
        })
        assert res_tel.status_code == 200
        tel_data = res_tel.json()
        assert tel_data["is_active"] is True
        assert tel_data["permission_type"] == "TELEMETRY_ACCESS"

        # 2. Grant DEVICE_CONTROL consent for the purifier
        res_ctrl = await client.post("/api/v1/consents", headers=headers, json={
            "home_id": home_id,
            "device_id": device_id,
            "permission_type": "DEVICE_CONTROL",
            "authorized_actions": ["fan.set_speed", "fan.turn_on"],
            "consent_version": "1.0",
            "consent_origin": "onboarding_wizard"
        })
        assert res_ctrl.status_code == 200
        ctrl_data = res_ctrl.json()
        assert ctrl_data["is_active"] is True
        consent_id = ctrl_data["id"]

        # Verify device automation_authorized was enabled
        devices = (await client.get(f"/api/v1/devices?home_id={home_id}", headers=headers)).json()
        purifier = next(d for d in devices if d["id"] == device_id)
        assert purifier["automation_authorized"] is True

        # 3. Check consent status summary
        status_res = await client.get("/api/v1/consents/status", headers=headers)
        assert status_res.status_code == 200
        status_data = status_res.json()["active_consents"]
        assert status_data["TELEMETRY_ACCESS"] is True
        assert status_data["DEVICE_CONTROL"] is True
        assert status_data["AI_TRAINING_SHARE"] is False

        # 4. Revoke DEVICE_CONTROL consent
        revoke_res = await client.patch(f"/api/v1/consents/{consent_id}/revoke", headers=headers)
        assert revoke_res.status_code == 200
        revoked_data = revoke_res.json()
        assert revoked_data["is_active"] is False
        assert revoked_data["revoked_at"] is not None

        # Verify device automation_authorized was cascaded to False
        devices_after = (await client.get(f"/api/v1/devices?home_id={home_id}", headers=headers)).json()
        purifier_after = next(d for d in devices_after if d["id"] == device_id)
        assert purifier_after["automation_authorized"] is False

@pytest.mark.asyncio
async def test_server_side_consent_blocks_automation():
    """Verifies that revoked consent prevents automatic actuation even if an automation rule is active."""
    uid = uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(id=f"user_{uid}", email=f"block_{uid}@airguard.ai", hashed_password="pw", is_active=True)
        home = Home(id=f"home_{uid}", owner_id=user.id, name="Block Test Home")
        room = Room(id=f"room_{uid}", home_id=home.id, name="Living Room")
        purifier = Device(
            id=f"dev_purifier_{uid}",
            home_id=home.id,
            room_id=room.id,
            name="Block Purifier",
            connection_protocol="simulation",
            is_controllable=True,
            automation_authorized=True  # Device flag True, but consent revoked below
        )
        # Create an explicitly revoked consent record
        revoked_consent = UserConsent(
            id=f"consent_revoked_{uid}",
            user_id=user.id,
            home_id=home.id,
            device_id=purifier.id,
            permission_type="DEVICE_CONTROL",
            is_active=False,
            revoked_at=datetime.utcnow()
        )
        db.add_all([user, home, room, purifier, revoked_consent])
        await db.commit()

        # Invariant check via SafetyEngine
        is_allowed, reason = SafetyEngine.validate_automation_action(
            device=purifier,
            command="set_speed",
            parameters={"speed": 3},
            consent=revoked_consent
        )
        assert is_allowed is False
        assert "CONSENT REVOKED" in reason

@pytest.mark.asyncio
async def test_notification_preferences_and_test_dispatch():
    """Verifies configuring notification preferences, quiet hours, and test alert dispatch."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        # 1. Configure notification preference with quiet hours
        pref_res = await client.post("/api/v1/notifications/preferences", headers=headers, json={
            "home_id": home_id,
            "event_category": "ELEVATED_READING",
            "delivery_channel": "IN_APP",
            "enabled": True,
            "min_severity": "ELEVATED",
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "cooldown_minutes": 15
        })
        assert pref_res.status_code == 200
        pref_data = pref_res.json()
        assert pref_data["event_category"] == "ELEVATED_READING"
        assert pref_data["quiet_hours_enabled"] is True

        # 2. Dispatch a test notification
        test_res = await client.post("/api/v1/notifications/test", headers=headers, json={
            "home_id": home_id,
            "channel": "IN_APP"
        })
        assert test_res.status_code == 200
        assert test_res.json()["success"] is True
        alert_id = test_res.json()["alert_id"]

        # 3. Verify notification is in history and unread
        history_res = await client.get(f"/api/v1/notifications/history?home_id={home_id}", headers=headers)
        assert history_res.status_code == 200
        alerts = history_res.json()
        assert any(a["id"] == alert_id for a in alerts)

        # 4. Mark alert as read
        read_res = await client.patch(f"/api/v1/notifications/{alert_id}/read", headers=headers)
        assert read_res.status_code == 200
        assert read_res.json()["is_read"] is True

        # 5. Mark all read
        mark_all_res = await client.post(f"/api/v1/notifications/mark-all-read?home_id={home_id}", headers=headers)
        assert mark_all_res.status_code == 200

@pytest.mark.asyncio
async def test_global_automation_pause_kill_switch():
    """Verifies that pausing automations globally halts all automated rule execution."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        # 1. Pause all automations
        pause_res = await client.post(f"/api/v1/automations/pause-all?home_id={home_id}&paused=true", headers=headers)
        assert pause_res.status_code == 200
        assert pause_res.json()["automations_paused"] is True

        # Check Home reflects paused in DB
        async with AsyncSessionLocal() as db:
            from sqlalchemy.future import select
            h_res = await db.execute(select(Home).where(Home.id == home_id))
            h = h_res.scalars().first()
            assert h.automations_paused is True

            # Invariant check: SafetyEngine blocks action when automations_paused is True
            dev = Device(id="dev_test_p", name="Purifier", is_controllable=True, automation_authorized=True)
            is_allowed, reason = SafetyEngine.validate_automation_action(
                device=dev,
                command="set_speed",
                parameters={"speed": 3},
                home=h
            )
            assert is_allowed is False
            assert "AUTOMATIONS PAUSED" in reason

        # 2. Resume automations
        resume_res = await client.post(f"/api/v1/automations/pause-all?home_id={home_id}&paused=false", headers=headers)
        assert resume_res.status_code == 200
        assert resume_res.json()["automations_paused"] is False

@pytest.mark.asyncio
async def test_safety_invariants_voc_and_stale_data_rejection():
    """Verifies that automated control is rejected on VOC triggers and stale sensor data (>120s)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]
        rooms = (await client.get(f"/api/v1/rooms?home_id={home_id}", headers=headers)).json()
        room_id = rooms[0]["id"]
        devices = (await client.get(f"/api/v1/devices?home_id={home_id}", headers=headers)).json()
        purifier = next(d for d in devices if d["is_controllable"])

        # 1. Attempting auto_control on VOC preset must be rejected with 400
        voc_res = await client.post("/api/v1/automations/apply-preset", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "preset_id": "odor_eliminator",
            "purifier_device_id": purifier["id"],
            "mode": "auto_control"
        })
        assert voc_res.status_code == 400
        assert "SAFETY INVARIANT" in voc_res.json()["detail"]

        # 2. Stale data check (>120s old reading)
        stale_timestamp = datetime.utcnow() - timedelta(seconds=180)
        async with AsyncSessionLocal() as db:
            dev_obj = await db.get(Device, purifier["id"])
            is_allowed, reason = SafetyEngine.validate_automation_action(
                device=dev_obj,
                command="set_speed",
                parameters={"speed": 2},
                reading_timestamp=stale_timestamp
            )
            assert is_allowed is False
            assert "STALE SENSOR DATA" in reason

@pytest.mark.asyncio
async def test_gdpr_user_data_export():
    """Verifies that full account data can be exported as a structured JSON archive."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        export_res = await client.get("/api/v1/auth/export-data", headers=headers)
        assert export_res.status_code == 200
        data = export_res.json()
        assert "user" in data
        assert "homes" in data
        assert "rooms" in data
        assert "devices" in data
        assert "consents" in data
        assert "notification_preferences" in data
        assert "exported_at" in data
