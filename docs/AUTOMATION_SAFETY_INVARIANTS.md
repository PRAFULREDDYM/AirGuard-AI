# AirGuard AI — Automation Safety Invariants

## Core Principles

AirGuard AI interacts with real environmental sensors and physical air treatment appliances. Because physical actuators have direct implications for occupant comfort, fire safety, and electrical integrity, all automations are governed by immutable safety invariants enforced at the API and engine levels.

---

## The 14 Immutable Invariants

### 1. Global Kill-Switch Invariant
When `home.automations_paused == True`, all automation execution is halted immediately across all rooms and devices. No actuator command can be dispatched until the user explicitly resumes automations.

### 2. Active Consent Invariant
Automated actuator control requires an active, unrevoked `DEVICE_CONTROL` consent record. If consent is revoked, all automation rules for that user's devices are nullified.

### 3. Device Authorization Invariant
Both `is_controllable` and `automation_authorized` flags must be `True` on the device model. Uncontrollable monitors or manually de-authorized purifiers will never be commanded.

### 4. Manual Override Hold
When a user manually adjusts fan speed or power state, the device enters a manual override hold for 60 minutes. The automation engine will not alter device state during an active override.

### 5. Conservative Emergency Suspension (`EMERGENCY_SUSPENDED`)
In the event of suspected fire, smoke, or combustible gas hazards, the system enters an emergency suspension state:
- All fan actuation is prohibited.
- Fans are never turned on or adjusted, preventing the risk of electrical ignition or accelerating oxygen flow into a fire.
- The UI surfaces prominent emergency warning guidance advising evacuation.

### 6. Particulate-Only Filtration Invariant
Automatic purifier speed increases are **strictly tied to particulate filtration** (PM2.5 / PM10). Automated fan speed adjustments in response to unvalidated VOC or odor predictions are strictly prohibited and rejected at the API boundary.

### 7. Sensor Freshness Invariant
Actuator decisions must be based on fresh telemetry. Readings older than 120 seconds are classified as stale and cannot trigger automation commands.

### 8. Strict Room Locality Invariant
A sensor in Room A can never trigger an actuator in Room B. Both devices must share the identical `room_id`.

### 9. Sensor Warmup Invariant
Readings recorded while a sensor is in its manufacturer warmup phase are excluded from triggering automation events.

### 10. Capability Verification Invariant
Commands dispatched to a device must match capabilities advertised in its `DeviceCapability` manifest. Unsupported controls (e.g. commanding oscillation on a non-oscillating purifier) are rejected.

### 11. Rate-Limiting & Cooldown Invariant
Device commands are rate-limited to a maximum of 1 command per device per 30-second window to prevent relay wear, motor stress, and network flooding.

### 12. Speed Ceiling Invariant
Target speed commands must fall within the device's allowable range (typically 1 to 3 or 1 to 4). Out-of-bounds speeds are clamped or rejected.

### 13. Command Idempotency Invariant
If a purifier is already operating at the desired speed, redundant duplicate commands are discarded without network dispatch.

### 14. Certified Alarm Independence Invariant
AirGuard AI never disables, mutes, or overrides certified life-safety alarms (smoke, carbon monoxide, gas detectors). AirGuard is not a life-safety certified appliance.

---

## Verification & Audit
All automation validation checks are executed inside `services.automation.safety.SafetyEngine.validate_automation_action` and verified through unit and integration test suites in `tests/integration/test_phase7_production_monitoring_and_onboarding.py`.
