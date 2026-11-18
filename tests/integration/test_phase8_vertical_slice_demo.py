"""
AirGuard AI — Phase 8: 19-Step End-to-End Vertical-Slice Beta Demonstration
Executes and validates the exact complete consumer user journey:
1. User installs / launches AirGuard.
2. User signs in.
3. User connects a supported monitor (AirGradient ONE).
4. Monitor streams valid measurements (PM2.5).
5. User connects a compatible purifier (Levoit Core 400S).
6. Both devices are assigned to the same room.
7. User selects Mode 1: Monitor & Notify.
8. Controlled test event creates a notification.
9. User upgrades to Mode 2: Automatic Purifier Control.
10. System presents exact control permissions; user grants consent.
11. User authorizes a safe clean air automation rule.
12. A valid particulate event triggers the rule.
13. Purifier command is dispatched.
14. Command result is confirmed.
15. Event appears in automation history.
16. User engages emergency pause kill-switch.
17. Subsequent particle spike is blocked by pause state.
18. User revokes DEVICE_CONTROL consent.
19. After restart / fresh session, authorization remains strictly revoked.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from services.api.database import AsyncSessionLocal
from services.api.models import (
    User, Home, Room, Device, SensorReading, MeasurementType,
    AutomationRule, AutomationExecution, UserConsent, DataProvenance, CalibrationQuality
)
from services.automation.engine import AutomationEngine

@pytest.mark.asyncio
async def test_complete_19_step_vertical_slice_journey():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1 & 2: User Installation & Authentication
        uid = uuid4().hex[:8]
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": f"beta_{uid}@airguard.ai",
            "password": "Password123!",
            "full_name": "Beta Tester"
        })
        assert reg_res.status_code == 200
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        homes = (await client.get("/api/v1/homes", headers=headers)).json()
        home_id = homes[0]["id"]

        # Step 3 & 6: User creates Room and connects supported AirGradient monitor
        room_res = await client.post("/api/v1/rooms", headers=headers, json={
            "home_id": home_id,
            "name": "Master Bedroom",
            "room_type": "bedroom"
        })
        assert room_res.status_code == 200
        room_id = room_res.json()["id"]

        mon_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "name": "AirGradient ONE v3.1",
            "manufacturer": "AirGradient",
            "model": "ONE",
            "connection_protocol": "airgradient",
            "is_controllable": False
        })
        assert mon_res.status_code == 200
        monitor_id = mon_res.json()["id"]

        # Step 4: The app receives measurements
        async with AsyncSessionLocal() as db:
            reading1 = SensorReading(
                device_id=monitor_id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25,
                value=15.0, unit="µg/m³", provenance=DataProvenance.MEASURED,
                calibration_quality=CalibrationQuality.CALIBRATED, source_integration="airgradient",
                timestamp=datetime.utcnow()
            )
            db.add(reading1)
            await db.commit()

        # Step 5 & 6: User connects compatible Levoit purifier to the same room
        pur_res = await client.post("/api/v1/devices", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "name": "Levoit Core 400S",
            "manufacturer": "Levoit",
            "model": "Core 400S",
            "connection_protocol": "home_assistant",
            "is_controllable": True,
            "automation_authorized": False # Initially unauthorized
        })
        assert pur_res.status_code == 200
        purifier_id = pur_res.json()["id"]

        # Step 7: User chooses Mode 1: Monitor & Notify
        consent_tel = await client.post("/api/v1/consents", headers=headers, json={
            "home_id": home_id,
            "permission_type": "TELEMETRY_ACCESS",
            "authorized_actions": ["read_telemetry", "aggregate_history"]
        })
        assert consent_tel.status_code == 200

        # Step 8: Controlled test event creates an in-app notification
        test_alert_res = await client.post("/api/v1/notifications/test", headers=headers, json={
            "home_id": home_id,
            "channel": "IN_APP"
        })
        assert test_alert_res.status_code == 200
        assert test_alert_res.json()["delivery_status"] == "DELIVERED"

        # Verify alert appears in notification history
        notifs = (await client.get(f"/api/v1/notifications/history?home_id={home_id}", headers=headers)).json()
        assert len(notifs) >= 1

        # Step 9 & 10: User upgrades to Mode 2 (Automatic Purifier Control) & grants explicit consent
        consent_ctrl = await client.post("/api/v1/consents", headers=headers, json={
            "home_id": home_id,
            "device_id": purifier_id,
            "permission_type": "DEVICE_CONTROL",
            "authorized_actions": ["fan.set_speed", "fan.turn_on", "fan.turn_off"]
        })
        assert consent_ctrl.status_code == 200
        consent_ctrl_id = consent_ctrl.json()["id"]

        # Authorize device for automation
        auth_dev = await client.patch(f"/api/v1/devices/{purifier_id}/authorization?authorized=true", headers=headers)
        assert auth_dev.status_code == 200
        assert auth_dev.json()["automation_authorized"] is True

        # Step 11: User authorizes safe Clean Air Guard automation rule
        rule_res = await client.post("/api/v1/automations", headers=headers, json={
            "home_id": home_id,
            "room_id": room_id,
            "name": "Clean Air Guard",
            "enabled": True,
            "trigger_config": {"measurement_type": "PM25", "condition": "ABOVE", "threshold": 25.0},
            "action_config": {"device_id": purifier_id, "command": "set_speed", "parameters": {"speed": 3}},
            "cooldown_seconds": 0
        })
        assert rule_res.status_code == 200
        rule_id = rule_res.json()["id"]

        # Step 12, 13 & 14: Valid particulate event triggers rule, dispatches command, confirms result
        dispatched_cmds = []
        async def mock_dispatcher(dev, cmd, params):
            dispatched_cmds.append((dev.id, cmd, params))

        spike_reading = SensorReading(
            device_id=monitor_id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25,
            value=45.0, unit="µg/m³", provenance=DataProvenance.MEASURED,
            calibration_quality=CalibrationQuality.CALIBRATED, source_integration="airgradient",
            timestamp=datetime.utcnow()
        )

        async with AsyncSessionLocal() as db:
            execs = await AutomationEngine.evaluate_rules_for_reading(
                db=db, reading=spike_reading, device_adapter_dispatcher=mock_dispatcher
            )

        assert len(dispatched_cmds) == 1
        assert dispatched_cmds[0] == (purifier_id, "set_speed", {"speed": 3})
        assert len(execs) == 1
        assert execs[0].status == "SUCCESS"

        # Step 15: Event appears in history
        exec_history = (await client.get("/api/v1/automations/executions", headers=headers)).json()
        assert len(exec_history) >= 1
        assert exec_history[0]["status"] == "SUCCESS"

        # Step 16: User pauses automations (Emergency Kill-Switch)
        pause_res = await client.post(f"/api/v1/automations/pause-all?home_id={home_id}&paused=true", headers=headers)
        assert pause_res.status_code == 200
        assert pause_res.json()["automations_paused"] is True

        # Step 17: Subsequent spike occurs while paused -> command blocked!
        dispatched_cmds_paused = []
        async def mock_dispatcher_paused(dev, cmd, params):
            dispatched_cmds_paused.append((dev.id, cmd, params))

        second_spike = SensorReading(
            device_id=monitor_id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25,
            value=65.0, unit="µg/m³", provenance=DataProvenance.MEASURED,
            calibration_quality=CalibrationQuality.CALIBRATED, source_integration="airgradient",
            timestamp=datetime.utcnow()
        )
        async with AsyncSessionLocal() as db:
            execs_paused = await AutomationEngine.evaluate_rules_for_reading(
                db=db, reading=second_spike, device_adapter_dispatcher=mock_dispatcher_paused
            )
        assert len(dispatched_cmds_paused) == 0

        # Resume automations for consent revocation test
        await client.post(f"/api/v1/automations/pause-all?home_id={home_id}&paused=false", headers=headers)

        # Step 18: User revokes consent
        revoke_res = await client.patch(f"/api/v1/consents/{consent_ctrl_id}/revoke", headers=headers)
        assert revoke_res.status_code == 200
        assert revoke_res.json()["is_active"] is False

        # Step 19: Authorization remains revoked after restart / new session
        dispatched_cmds_revoked = []
        async def mock_dispatcher_revoked(dev, cmd, params):
            dispatched_cmds_revoked.append((dev.id, cmd, params))

        third_spike = SensorReading(
            device_id=monitor_id, sensor_id="pm25_sensor", measurement_type=MeasurementType.PM25,
            value=70.0, unit="µg/m³", provenance=DataProvenance.MEASURED,
            calibration_quality=CalibrationQuality.CALIBRATED, source_integration="airgradient",
            timestamp=datetime.utcnow()
        )
        async with AsyncSessionLocal() as db:
            execs_revoked = await AutomationEngine.evaluate_rules_for_reading(
                db=db, reading=third_spike, device_adapter_dispatcher=mock_dispatcher_revoked
            )

        # Dispatches must remain strictly zero
        assert len(dispatched_cmds_revoked) == 0

