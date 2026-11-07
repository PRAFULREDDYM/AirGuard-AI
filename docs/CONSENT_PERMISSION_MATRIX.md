# AirGuard AI — Consent & Permissions Matrix

## Overview

AirGuard AI complies with GDPR, CCPA, and best-practice IoT privacy standards. Permissions are **unbundled**, versioned, stored in the database (`user_consents` table), and revocable at any time.

---

## Permission Definitions

| Permission Key | Purpose | Required For | Default Value | Revocation Impact |
| :--- | :--- | :--- | :--- | :--- |
| `TELEMETRY_ACCESS` | Reading and storing sensor measurements (PM2.5, VOC, CO2, Temp, RH). | Monitor & Notify, Auto Control | `True` | Stops recording history and real-time dashboard charts. |
| `PUSH_NOTIFICATIONS` | Sending alerts and threshold excursion notices via in-app & push. | Alerts, Daily Summaries | `True` | Alerts are suppressed; only system logs are retained. |
| `DEVICE_CONTROL` | Sending actuator commands (fan speed, power) to verified purifiers. | Mode 2: Auto Control | `False` | Halts all automatic purifier actuation immediately. |
| `CLOUD_PROCESSING` | Optional off-premises telemetry backup and remote sync. | Remote Dashboard Access | `False` | Retains all telemetry purely inside the local network. |
| `AI_TRAINING_SHARE` | Sharing anonymized sensor readings to improve ML calibration. | Open Source ML Research | `False` | Sensor recordings are never included in training corpuses. |

---

## Server-Side Revocation Cascade

When a user revokes `DEVICE_CONTROL` from `/settings` or during onboarding:
1. `PATCH /api/v1/consents/{id}/revoke` marks the consent record as `is_active=False` and timestamps `revoked_at`.
2. All connected devices owned by the user have `automation_authorized` set to `False`.
3. In-flight automation rules mapped to the user's purifiers are deactivated.
4. Any subsequent automated actuation command intercepted by `SafetyEngine.validate_automation_action` is rejected with:
   `"CONSENT REVOKED: User has explicitly revoked permission to control physical devices."`

---

## Versioning & Audit Trail

- Each consent entry records:
  - `user_id` (UUID)
  - `permission_type` (Enum)
  - `authorized_actions` (JSON array of strings)
  - `consent_version` (Semantic version string, e.g., `"v1.0"`)
  - `is_active` (Boolean)
  - `created_at` (Timestamp)
  - `revoked_at` (Nullable timestamp)
- An immutable log of all consent changes is appended to `audit_logs` for regulatory compliance.

---

## Data Subject Rights (GDPR / CCPA)

- **Right of Access / Portability**: `GET /api/v1/auth/export-data` exports an exhaustive JSON archive containing user profile, homes, rooms, devices, rules, consents, and notification settings.
- **Right to Erasure**: `DELETE /api/v1/auth/delete-account-data` executes a permanent cascade deletion of all user records, sensor readings, and credentials.
