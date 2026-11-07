# AirGuard AI — Automation Race Condition & Command Hardening Tests

## Overview

In IoT automation, asynchronous message ingestion, queued command queues, and background thread execution introduce potential race conditions where a user action (such as pausing automations or revoking device control consent) occurs *after* a sensor reading triggers an evaluation, but *before* physical actuator commands are sent.

AirGuard AI Phase 8 introduces an **Atomic Pre-Dispatch Recheck** at the boundary of device command dispatch to guarantee that no queued or in-flight commands can bypass newly asserted user safety constraints.

---

## 1. Attack / Hazard Vectors Mitigated

| Vector | Failure Scenario Without Hardening | Phase 8 Pre-Dispatch Recheck Behavior |
| :--- | :--- | :--- |
| **Mid-flight Consent Revocation** | User clicks "Revoke Device Control" while high-PM2.5 evaluation is queued; fan speed command is sent anyway. | Re-queries `UserConsent` immediately before dispatch; detects `is_active=False` and blocks dispatch with `BLOCKED_BY_SAFETY`. |
| **Mid-flight Emergency Kill-Switch** | User clicks global "Pause All Automations" kill-switch during an active event; command still executes. | Re-queries `Home` immediately before dispatch; detects `automations_paused=True` and blocks dispatch. |
| **Physical Button Manual Override** | User physically pushes purifier button to set Low speed while background task attempts to boost fan; automation silently overrides user. | Re-queries `Device` immediately before dispatch; detects `manual_override=True` and preserves user hold for 60 minutes. |
| **Device Authorization Deselection** | User untoggles "Allow AirGuard to control this purifier"; in-flight rule still actuates. | Re-queries `Device` immediately before dispatch; detects `automation_authorized=False` and halts. |

---

## 2. Test Execution & Evidence

- **Test Suite**: `tests/integration/test_automation_race_conditions.py`
- **Results**:
  - `test_race_condition_consent_revoked_at_dispatch`: **PASSED** (Zero commands dispatched; execution status `BLOCKED_BY_SAFETY`).
  - `test_race_condition_pause_killswitch_at_dispatch`: **PASSED** (Zero commands dispatched; execution status `BLOCKED_BY_SAFETY`).
  - `test_race_condition_manual_override_at_dispatch`: **PASSED** (Zero commands dispatched; execution status `BLOCKED_BY_SAFETY`).
- **Summary**: 3/3 tests passed in 0.33s.
