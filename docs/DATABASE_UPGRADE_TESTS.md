# AirGuard AI — Database Migration & Schema Upgrade Verification Report

## Overview

This document details the schema migration architecture, execution results, and data-integrity guarantees for upgrading existing populated databases to the Phase 8 Consumer Beta schema (`revision: c8f1e31d45ab`).

---

## 1. Migration Lineage

```
[ b9ee59aedd6b ] (Initial baseline)
        │
        ▼
[ c8f1e31d45ab ] (Phase 8 Consumer Beta: Consents, Notifications, Pause State, Guard Columns)
```

---

## 2. Changes Applied in `c8f1e31d45ab`

### Tables Created
1. **`user_consents`**:
   - `id VARCHAR(36) PRIMARY KEY`
   - `user_id VARCHAR(36) REFERENCES users(id)`
   - `home_id VARCHAR(36) REFERENCES homes(id)`
   - `device_id VARCHAR(36) REFERENCES devices(id)`
   - `integration_scope VARCHAR(100)`
   - `permission_type VARCHAR(50) NOT NULL` (e.g. `DEVICE_CONTROL`, `TELEMETRY_ACCESS`)
   - `authorized_actions JSON`
   - `consent_version VARCHAR(20) DEFAULT '1.0'`
   - `consent_origin VARCHAR(100) DEFAULT 'onboarding_wizard'`
   - `is_active BOOLEAN DEFAULT 1`
   - `created_at`, `expires_at`, `revoked_at DATETIME`

2. **`notification_preferences`**:
   - `id VARCHAR(36) PRIMARY KEY`
   - `user_id VARCHAR(36) REFERENCES users(id)`
   - `home_id VARCHAR(36) REFERENCES homes(id)`
   - `room_id VARCHAR(36) REFERENCES rooms(id)`
   - `device_id VARCHAR(36) REFERENCES devices(id)`
   - `event_category VARCHAR(50) NOT NULL`
   - `delivery_channel VARCHAR(50) DEFAULT 'IN_APP'`
   - `enabled BOOLEAN DEFAULT 1`
   - `min_severity VARCHAR(50) DEFAULT 'ELEVATED'`
   - `quiet_hours_enabled BOOLEAN DEFAULT 0`
   - `quiet_hours_start VARCHAR(5) DEFAULT '22:00'`
   - `quiet_hours_end VARCHAR(5) DEFAULT '07:00'`
   - `cooldown_minutes INTEGER DEFAULT 15`
   - `last_notified_at`, `created_at DATETIME`

3. **`push_subscriptions`**:
   - `id VARCHAR(36) PRIMARY KEY`
   - `user_id VARCHAR(36) REFERENCES users(id)`
   - `endpoint TEXT UNIQUE NOT NULL`
   - `p256dh_key VARCHAR(255) NOT NULL`
   - `auth_key VARCHAR(255) NOT NULL`
   - `user_agent VARCHAR(255)`
   - `is_active BOOLEAN DEFAULT 1`
   - `created_at DATETIME`

### Columns Added
- **`homes`**: `automations_paused BOOLEAN DEFAULT 0`
- **`devices`**:
  - `automation_authorized BOOLEAN DEFAULT 0`
  - `manual_override BOOLEAN DEFAULT 0`
  - `manual_override_until DATETIME`
- **`alerts`**:
  - `room_id VARCHAR(36)`
  - `device_id VARCHAR(36)`
  - `category VARCHAR(50) DEFAULT 'ELEVATED_READING'`
  - `delivery_channel VARCHAR(50) DEFAULT 'IN_APP'`
  - `delivery_status VARCHAR(50) DEFAULT 'DELIVERED'`
  - `delivery_attempts INTEGER DEFAULT 1`
  - `failure_reason TEXT`
  - `acknowledged_at DATETIME`
  - `read_at DATETIME`

---

## 3. Automated Upgrade Test Verification

- **Test Suite**: `tests/integration/test_database_migrations.py`
- **Methodology**:
  1. Spun up an isolated SQLite test database with pre-existing populated records (`users`, `homes`, `devices`, `alerts`) pinned to `b9ee59aedd6b`.
  2. Executed `alembic upgrade head` programmatically.
  3. Verified that all existing records were retained without data corruption.
  4. Verified that all new tables and columns were queryable with proper default values.
  5. Confirmed `alembic_version` updated to `c8f1e31d45ab`.
- **Result**: `1 passed in 0.21s`. Zero data loss.
