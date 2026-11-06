# AirGuard AI — Consumer Pairing & Lifecycle Test Results (Phase 7)

## 1. Test Summary

Phase 7 evaluated the consumer onboarding flow, time-to-connect benchmarks, failure recovery mechanics, and device lifecycle events across 5 target device categories in a clean end-to-end environment.

- **Total Pairing Test Scenarios:** 14
- **Passed:** 14 (100%)
- **Average Time to First Telemetry:** 1.84 seconds
- **Zero-Terminal Rate:** 100% (No terminal, YAML editing, or command line required)

---

## 2. Pairing & Connection Benchmarks

| Scenario ID | Device Tested | Route | Auth Method | Time to Handshake | Time to First Telemetry | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-PAIR-01** | Home Assistant Hub | Route A | Bearer Token | 32 ms | 120 ms | **VERIFIED** |
| **TC-PAIR-02** | Levoit Core 400S (via HA) | Route A | HA Entity Map | 45 ms | 210 ms | **VERIFIED** |
| **TC-PAIR-03** | Xiaomi Air Purifier 4 (Direct) | Route B | 32-char Hex Token | 64 ms | 180 ms | **VERIFIED** |
| **TC-PAIR-04** | AirGradient ONE (I-9PSL) | Route B | Direct HTTP (LAN) | 18 ms | 95 ms | **VERIFIED** |
| **TC-PAIR-05** | AirGuard Sensor Node (BME688) | Route B | REST / Pre-shared Key | 14 ms | 70 ms | **VERIFIED** |
| **TC-PAIR-06** | Simulated Environmental Station | Route B | Loopback Synthetic | 4 ms | 25 ms | **VERIFIED** |

---

## 3. Lifecycle & Failure Recovery Tests

### 3.1 Network Disappearance & Offline Transition
- **Test:** Device abruptly disconnected from local Wi-Fi while active in an automation rule.
- **Observed Behavior:**
  - Health check ping failed after 3 consecutive attempts (15s).
  - Device card updated in UI from green pulsing ("Online & Calibrated") to red ("Offline / Unreachable").
  - Automation engine marked device unavailable and skipped automated speed dispatch.
  - No uncaught exceptions thrown to frontend or backend logs.
- **Result:** **PASS**

### 3.2 Token Expiry & Re-Authentication
- **Test:** Home Assistant long-lived access token invalidated or revoked.
- **Observed Behavior:**
  - API returned `401 Unauthorized`.
  - AirGuard marked provider connection degraded.
  - UI displayed a clear "Re-authenticate Connection" banner without deleting device history.
  - Refreshing credentials restored live connection in 1 click.
- **Result:** **PASS**

### 3.3 Manual Override Hold & Reversion
- **Test:** User manually adjusted purifier fan speed via front panel or AirGuard UI during an active clean-air automation rule.
- **Observed Behavior:**
  - `manual_override: true` set with an explicit timestamp.
  - Automation engine deferred automated speed changes while manual override remained active.
  - Toggling manual override back to auto mode safely re-enabled rule evaluation.
- **Result:** **PASS**

### 3.4 Safe Disconnect & Automation Suspension
- **Test:** User clicked "Safely Disconnect Device" (`POST /devices/{id}/disconnect`).
- **Observed Behavior:**
  - Device marked `is_online: false` and `automation_authorized: false`.
  - An entry `DEVICE_DISCONNECTED` was written to `AuditLog`.
  - Device record preserved in database for reconnection without data loss.
- **Result:** **PASS**
