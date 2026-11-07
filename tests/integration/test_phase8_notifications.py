"""
AirGuard AI — Phase 8: Notification Delivery, Push Subscriptions, ACK & Offline Monitoring Tests
Tests:
- Web Push API subscription registration & storage.
- Notification delivery acknowledgment (client ACK transitions delivery_status to DELIVERED).
- Device-offline health scanner: detects stale telemetry, marks device offline, creates WARNING alert.
- Alert deduplication: prevents spamming duplicate offline alerts within cooldown period.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from services.api.database import AsyncSessionLocal
from services.api.models import User, Home, Room, Device, Alert, EventSeverity

@pytest.mark.asyncio
async def test_push_subscription_and_delivery_acknowledgment():
    """Verifies Web Push subscription registration and client delivery ACK endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/demo-login")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        # 1. Register a Web Push Subscription
        sub_payload = {
            "endpoint": f"https://updates.push.services.mozilla.com/wpush/v2/{uuid4().hex}",
            "p256dh_key": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9ic0WA",
            "auth_key": "tBHItJI5svbpez7KI4CCXg",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        sub_res = await client.post("/api/v1/notifications/push-subscribe", headers=headers, json=sub_payload)
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert sub_data["endpoint"] == sub_payload["endpoint"]
        assert sub_data["is_active"] is True

        # 2. Dispatch a Test Push Notification
        test_res = await client.post("/api/v1/notifications/test", headers=headers, json={
            "home_id": home_id,
            "channel": "PUSH_NOTIFICATION"
        })
        assert test_res.status_code == 200
        alert_id = test_res.json()["alert_id"]
        assert test_res.json()["delivery_status"] == "PENDING_CLIENT_CONFIRMATION"

        # 3. Client Acknowledges Delivery
        ack_res = await client.post(f"/api/v1/notifications/{alert_id}/ack", headers=headers)
        assert ack_res.status_code == 200
        ack_data = ack_res.json()
        assert ack_data["alert_id"] == alert_id
        assert ack_data["delivery_status"] == "DELIVERED"
        assert ack_data["acknowledged_at"] is not None

@pytest.mark.asyncio
async def test_device_offline_detection_and_deduplication():
    """Verifies that stale devices are marked offline and deduplicated alerts are created."""
    uid = uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(id=f"u_{uid}", email=f"dev_{uid}@airguard.ai", hashed_password="pw", is_active=True)
        home = Home(id=f"h_{uid}", owner_id=user.id, name="Health Home")
        room = Room(id=f"r_{uid}", home_id=home.id, name="Bedroom")
        stale_device = Device(
            id=f"stale_{uid}", home_id=home.id, room_id=room.id, name="Old Sensor",
            manufacturer="Awair", model="Element", connection_protocol="rest",
            is_controllable=False, is_online=True,
            last_seen_at=datetime.utcnow() - timedelta(seconds=600)  # 10 minutes stale
        )
        db.add_all([user, home, room, stale_device])
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Authenticate
        from services.api.security import create_access_token
        token = create_access_token(data={"sub": user.id, "email": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Trigger health scan (timeout=300s)
        scan_res = await client.post(f"/api/v1/notifications/check-device-health?home_id={home.id}&timeout_seconds=300", headers=headers)
        assert scan_res.status_code == 200
        scan_data = scan_res.json()
        assert scan_data["offline_alerts_created"] == 1
        assert "Old Sensor" in scan_data["offline_devices"]

        # 2. Trigger second scan immediately: must deduplicate and NOT create another alert
        scan_res2 = await client.post(f"/api/v1/notifications/check-device-health?home_id={home.id}&timeout_seconds=300", headers=headers)
        assert scan_res2.status_code == 200
        scan_data2 = scan_res2.json()
        assert scan_data2["offline_alerts_created"] == 0 # Deduplicated!
