# AirGuard AI — Phase 8: Notification Delivery, Push Subscriptions & Offline Monitoring Tests

## Overview

AirGuard AI delivers multi-channel notifications across **In-App Toast/Notification Center** and **Web Push Subscriptions**. Phase 8 establishes delivery acknowledgment, Web Push key management, device-offline monitoring, alert deduplication, and honest delivery state reporting.

---

## 1. Notification Architecture & Channels

```
[ Environmental / Device Event ]
               │
               ▼
   [ Category & Preference Filter ] ──(Quiet Hours / Disabled)──> SUPPRESSED
               │
               ▼
      [ Cooldown Filter ] ──(<15m Duplicate)──> SUPPRESSED_COOLDOWN
               │
               ▼
      [ Channel Dispatch ]
        ├── IN_APP ───────► Status: DELIVERED
        └── WEB_PUSH ─────► Status: PENDING_CLIENT_CONFIRMATION
                                   │
                                   ▼
                         [ Client POST /ack ] ──► Status: DELIVERED
```

### Non-Fabricated Delivery Guarantee
- Notifications dispatched to Web Push or mobile endpoints are initialized with `delivery_status = "PENDING_CLIENT_CONFIRMATION"`.
- The status transitions to `DELIVERED` **only** after the client browser receives the payload and dispatches a delivery confirmation via `POST /api/v1/notifications/{alert_id}/ack`.
- AirGuard AI never marks a push notification as delivered simply because it was queued in a background task.

---

## 2. Web Push API Subscriptions (`POST /push-subscribe`)
- Stores user browser push endpoints, ECDH `p256dh` public keys, and HMAC `auth` secrets in the `push_subscriptions` table.
- Associates subscriptions strictly with authenticated user identity (`user_id`).
- Supports multi-device subscriptions (desktop + mobile browser).

---

## 3. Automated Device-Offline Detection (`POST /check-device-health`)
- Scans connected devices across a home for heartbeat / telemetry staleness:
  - Compares current time against `device.last_seen_at`.
  - If delta exceeds timeout (default 300 seconds), marks `device.is_online = False`.
  - Generates a `WARNING` notification under category `OFFLINE_SENSOR`.
- **Deduplication Invariant:**
  - If an offline alert has already been generated for this device within the last 30 minutes, subsequent health scans suppress duplicate alert generation, preventing notification flooding while hardware remains disconnected.

---

## 4. Test Verification Summary

- **Test Suite**: `tests/integration/test_phase8_notifications.py`
- **Results**:
  - `test_push_subscription_and_delivery_acknowledgment`: **PASSED** (200 OK, active subscription, ACK transition to `DELIVERED`).
  - `test_device_offline_detection_and_deduplication`: **PASSED** (200 OK, detects stale device, generates warning, suppresses duplicate on immediate re-scan).
- **Execution Time**: 2 passed in 2.06s.
