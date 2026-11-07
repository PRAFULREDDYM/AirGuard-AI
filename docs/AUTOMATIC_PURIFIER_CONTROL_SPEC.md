# AirGuard AI — Mode 2: Automatic Purifier Control Specification

## Overview

**Automatic Purifier Control** expands AirGuard AI's capabilities by enabling closed-loop, automated speed adjustments on verified air purifiers in response to environmental conditions. This mode is subject to strict, non-negotiable safety invariants to prevent unintended harm, equipment damage, or electrical ignition hazards.

---

## Authorization & Prerequisites

To enable Automatic Purifier Control, all of the following conditions must be met:
1. The user explicitly selects **Automatic Purifier Control** during Onboarding or in Room Settings.
2. An active, unrevoked `DEVICE_CONTROL` consent record exists in `user_consents`.
3. The target purifier has `is_controllable=True` and `automation_authorized=True`.
4. The target purifier and the triggering sensor are assigned to the **exact same physical room**.
5. Global automations are not paused (`home.automations_paused == False`).

---

## 14-Step Safety Validation Chain

Before any command is dispatched to an air purifier adapter (Home Assistant, local REST, or simulation), the `SafetyEngine.validate_automation_action` executes the following sequence:

```
[ Incoming Automation Trigger ]
             │
             ▼
[ 1. Global Kill-Switch Check ] ──(Paused)──> REJECT (HOME_AUTOMATIONS_PAUSED)
             │
             ▼
[ 2. Active User Consent Check ] ──(Revoked/None)──> REJECT (CONSENT_REVOKED)
             │
             ▼
[ 3. Device Controllable Flag ] ──(False)──> REJECT (DEVICE_NOT_CONTROLLABLE)
             │
             ▼
[ 4. Device Authorized Flag ] ──(False)──> REJECT (DEVICE_NOT_AUTHORIZED)
             │
             ▼
[ 5. Manual Override Hold ] ──(Active)──> REJECT (MANUAL_OVERRIDE_ACTIVE)
             │
             ▼
[ 6. Conservative Emergency State ] ──(Active)──> REJECT (EMERGENCY_SUSPENDED)
             │
             ▼
[ 7. Particulate Restriction ] ──(VOC/Odor Trigger)──> REJECT (VOC_CONTROL_PROHIBITED)
             │
             ▼
[ 8. Sensor Reading Freshness ] ──(>120s)──> REJECT (STALE_SENSOR_DATA)
             │
             ▼
[ 9. Sensor-Purifier Room Match ] ──(Mismatch)──> REJECT (ROOM_MISMATCH)
             │
             ▼
[ 10. Sensor Warmup Check ] ──(Warming Up)──> REJECT (SENSOR_WARMING_UP)
             │
             ▼
[ 11. Command Capability Support ] ──(Unsupported)──> REJECT (COMMAND_UNSUPPORTED)
             │
             ▼
[ 12. Rate-Limiting / Cooldown ] ──(<30s since last)──> REJECT (RATE_LIMITED)
             │
             ▼
[ 13. Speed Ceiling Verification ] ──(Invalid speed)──> REJECT (SPEED_OUT_OF_BOUNDS)
             │
             ▼
[ 14. Action Idempotency Check ] ──(Already at state)──> NO-OP (ALREADY_TARGET_STATE)
             │
             ▼
[ DISPATCH COMMAND TO ADAPTER ]
```

---

## Recovery & Step-Down Thresholds

To prevent rapid cycling (hunting) between fan speeds:
- **PM2.5 Step-Up Threshold**: Triggered when PM2.5 exceeds $35\ \mu\text{g}/\text{m}^3$ (Speed 2) or $55\ \mu\text{g}/\text{m}^3$ (Speed 3).
- **Hysteresis / Recovery Threshold**: Fan speed is only stepped down when PM2.5 drops below $20\ \mu\text{g}/\text{m}^3$ and remains below for at least 3 consecutive cycles (3 minutes).
- **Minimum Dwell Time**: Fan remains at an elevated speed for at least 180 seconds before decrementing.

---

## Manual Override Semantics

When a user manually modifies the purifier fan speed (either on physical hardware or in the AirGuard UI):
1. `manual_override` is set to `True`.
2. `manual_override_until` is set to $t + 60\text{ minutes}$.
3. The automation engine will **never** override the user's manual setting until the override expires or the user explicitly taps "Resume Automation".

