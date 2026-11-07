# AirGuard AI — Phase 8: Gap Audit & Verification Report

## Executive Summary

This audit assesses the state of AirGuard AI following the completion of Phase 7, systematically inspecting every subsystem, API router, database model, automation workflow, and user interface component against production-grade beta criteria.

---

## 1. Audit Findings by Priority Area

### A. Onboarding Flow & State Persistence
- **Current State:** The 8-stage unified onboarding wizard (`/onboarding`) renders all steps: Stage 1 (Welcome & Limits), Stage 2 (Connect Devices), Stage 3 (Verify Connections), Stage 4 (Assign Rooms), Stage 5 (Select Mode), Stage 6 (Permissions & Consent), Stage 7 (Dry-Run & Test), and Stage 8 (Activation).
- **Identified Gaps:**
  - In-flight onboarding state was held exclusively in component memory. If a consumer accidentally refreshed their browser during Stage 4 or 6, they had to start over from Stage 1.
  - *Remediation in Phase 8:* Add `localStorage` state restoration for in-flight onboarding sessions so interrupted setups can be resumed immediately without data loss.

### B. Server-Side Enforcement of Dual Operating Modes
- **Current State:**
  - **Mode 1 (Monitor & Notify):** `DEVICE_CONTROL` permission is not granted.
  - **Mode 2 (Automatic Purifier Control):** Requires active `UserConsent`, particulate-only triggers, room locality, and unpaused automations.
- **Identified Gaps:**
  - While `SafetyEngine.validate_automation_action` checked consent, in asynchronous or queued execution environments, if a user revoked consent or paused automations *after* an event was evaluated but *before* command dispatch, the command could theoretically dispatch.
  - *Remediation in Phase 8:* Implement an atomic pre-dispatch recheck immediately prior to physical adapter command execution.

### C. Notifications Subsystem
- **Current State:** In-app notification center, user preferences by category/channel, quiet hours, cooldowns, and test alerts are implemented in `services/api/routers/notifications.py`.
- **Identified Gaps:**
  - **Delivery Acknowledgment:** Test alerts set status to `DELIVERED` (in-app) or `PENDING_CLIENT_CONFIRMATION` (push), but there was no client acknowledgment endpoint (`POST /notifications/{id}/ack`) to confirm client receipt.
  - **Push Subscriptions:** Missing storage and schema for Web Push API subscriptions (`p256dh`, `auth`, `endpoint`).
  - **Device-Offline Alerts:** No background detection loop that flags a device whose `last_seen_at` exceeds the timeout threshold and generates a deduplicated warning alert.
  - *Remediation in Phase 8:* Add push subscription models, delivery ACK endpoint, and device-offline heartbeat monitor.

### D. Security & Production Hardening
- **Current State:** Local gateway incorporates SSRF filtering and AES-256-GCM credential encryption.
- **Identified Gaps:**
  - `POST /api/v1/auth/demo-login` was accessible unconditionally regardless of environment.
  - `mock_router` (providing `/mock-providers/ha` and `/mock-providers/airgradient`) was mounted unconditionally in `services/api/main.py`.
  - In production (`ENVIRONMENT=production`), mock provider endpoints and demo login bypass must be strictly disabled.
  - *Remediation in Phase 8:* Add environment-aware guards that reject demo logins and mock routes when `ENVIRONMENT == "production"` or `ENABLE_MOCK_PROVIDERS == False`.

### E. Database Schema & Migrations
- **Current State:** SQLite table alteration was performed using an ad-hoc migration script in Phase 7. Alembic only contained an empty skeleton migration (`b9ee59aedd6b_initial_schema.py`).
- **Identified Gaps:** Upgrading an existing populated database via `alembic upgrade head` failed to create `user_consents`, `notification_preferences`, `push_subscriptions`, or add columns (`automations_paused`, new alert/device fields).
- *Remediation in Phase 8:* Create standard Alembic migration scripts supporting both SQLite and PostgreSQL.

### F. Installation & Consumer Packaging
- **Current State:** Running AirGuard AI required manual virtualenv setup, pip installation, node package management, and two separate terminal sessions.
- **Identified Gaps:** Inaccessible to non-technical users. Requires an automated macOS application bundle, launchd daemon, and unified background control CLI (`airguard-ctl`).
- *Remediation in Phase 8:* Provide a self-contained macOS installer, LaunchAgent daemon plist, desktop application bundle, and diagnostic control tool.

### G. Scientific Honesty & ML Limitations
- **Current State:** Odor ML benchmarks reported in documentation.
- **Identified Gaps:** UI tabs in `/models` needed explicit, unmissable callouts emphasizing that the environmental odor classifier achieves ~51.62% balanced accuracy on unseen sessions, is an experimental prototype only, and cannot be used to actuate appliances.
- *Remediation in Phase 8:* Embed persistent warning banners on both the E-Nose and Environmental ML tabs.

---

## 2. Gap Remediation Action Plan

| Priority | Action Item | Target Files | Verification Method |
| :--- | :--- | :--- | :--- |
| **P1** | Document audit findings | `docs/PHASE8_GAP_AUDIT.md` | Verification review |
| **P2** | macOS installer, launchd service, and `airguard-ctl` CLI | `scripts/install_macos.sh`, `scripts/airguard-ctl` | Build and install verification |
| **P3** | Prove existing-device connectivity matrix | `docs/REAL_DEVICE_VALIDATION_STATUS.md` | Connectivity test suite |
| **P4** | Complete notification subscriptions, delivery ACK & offline monitor | `services/api/models/__init__.py`, `routers/notifications.py` | Notification test suite |
| **P5** | Pre-dispatch safety recheck & race condition prevention | `services/automation/engine.py`, `tests/integration/` | Race condition tests |
| **P6** | Alembic migrations & production security hardening | `alembic/versions/`, `services/api/config.py`, `main.py` | Database upgrade test |
| **P7** | LocalStorage state restore in Onboarding UI | `apps/web/src/app/onboarding/page.tsx` | Playwright test |
| **P8** | 19-Step Vertical-Slice demonstration | `docs/CONSUMER_BETA_ACCEPTANCE.md` | Acceptance test script |
| **P9** | Scientific Honesty notices in UI | `apps/web/src/app/models/page.tsx` | UI verification |
