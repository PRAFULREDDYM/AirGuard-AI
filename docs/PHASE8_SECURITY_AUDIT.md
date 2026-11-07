# AirGuard AI — Phase 8: Comprehensive Security & Privacy Audit Report

## Executive Summary

This security audit inspects AirGuard AI's attack surface across authentication, authorization, integration credential management, network SSRF protection, database encryption, GDPR/CCPA compliance, and production isolation.

---

## 1. Security Architecture & Threat Model

### A. Secret & Credential Storage
- **Mechanism:** All third-party credentials (Home Assistant long-lived access tokens, MQTT passwords, AirGradient tokens) are encrypted with **AES-256-GCM** using an authenticated encryption envelope prior to storage in `connections.encrypted_credentials`.
- **Key Hygiene:** Dev keys are strictly segregated from production environments. In production, `SECRET_KEY` and `ENCRYPTION_KEY` must be loaded from secure environment variables or vault backends.
- **Log Sanitation:** Plaintext passwords, tokens, and encryption keys are stripped before generating API response payloads or logging events to `audit_logs`.

### B. Cross-User & Cross-Home Authorization (IDOR Defense)
- **Tenant Isolation:** Every protected API endpoint inspects the authenticated JWT token (`sub = user_id`) and queries records using explicit ownership joins:
  - `Home.owner_id == current_user.id`
  - `Room.home_id == Home.id WHERE Home.owner_id == current_user.id`
  - `Device.home_id == Home.id WHERE Home.owner_id == current_user.id`
  - `Alert.home_id == Home.id WHERE Home.owner_id == current_user.id`
- Attempting to query, mutate, control, or delete devices belonging to another user results in an immediate `404 Not Found` or `403 Forbidden`.

### C. SSRF & Network Gateway Isolation
- **Discovery Restrictions:** The local network gateway (`services/api/routers/gateway.py`) scans local subnets for IoT beacons. To prevent Server-Side Request Forgery (SSRF) and cloud metadata exfiltration:
  - Blocks AWS/GCP/Azure link-local metadata addresses (`169.254.169.254`, `metadata.google.internal`).
  - Restricts discovery probing exclusively to whitelisted IoT service ports (`80, 8080, 8123, 9926, 6053, 1883, 8883, 8000`).
  - Rejects WAN public IP addresses from local gateway scan ranges.

### D. Production Mock Disabling & Demo Isolation
- **Environment Flag:** `services/api/config.py` defines `ENABLE_MOCK_PROVIDERS` and `is_production`.
- **Production Guard:**
  - When `is_production == True`, `mock_router` (which serves `/mock-providers/ha` and `/mock-providers/airgradient`) is **not mounted** in `services/api/main.py`.
  - `POST /api/v1/auth/demo-login` rejects authentication with `403 Forbidden` (`Demo auto-login is disabled in production environments`).

### E. GDPR & CCPA Compliance Architecture
- **Right to Portability:** `GET /api/v1/auth/export-data` extracts an immutable, structured JSON archive containing:
  - User profile
  - Associated homes and rooms
  - Connected devices and hardware capabilities
  - Active and historical automation rules
  - Versioned consent records
  - User notification preferences
- **Right to Erasure:** `DELETE /api/v1/auth/delete-account-data` executes a database-level cascading deletion of all associated tables (`User`, `Home`, `Room`, `Device`, `SensorReading`, `Alert`, `UserConsent`, `PushSubscription`).
- **Data Retention & Backups:** Telemetry older than configurable retention windows (default 90 days) is subject to automatic pruning. SQLite backup snapshots are recommended daily to encrypted volume mounts.

---

## 2. Security Test Evidence

| Test Suite | Coverage Area | Result |
| :--- | :--- | :--- |
| `tests/integration/test_phase7_consumer_connectivity.py` | SSRF metadata filtering & cross-home IDOR defense | **PASSED** |
| `tests/integration/test_phase7_production_monitoring_and_onboarding.py` | GDPR export data structure & cascade consent revocation | **PASSED** |
| `tests/integration/test_automation_race_conditions.py` | Command authorization pre-dispatch recheck | **PASSED** |
| `tests/integration/test_phase8_notifications.py` | Delivery acknowledgment & device offline alert deduplication | **PASSED** |

---

## 3. Deployment Checklist for Production Beta

1. Set `ENVIRONMENT="production"`.
2. Supply cryptographically random 32-byte keys for `SECRET_KEY` and `ENCRYPTION_KEY`.
3. Configure PostgreSQL connection string `DATABASE_URL="postgresql+asyncpg://..."`.
4. Ensure TLS/HTTPS termination at reverse proxy (Caddy, Nginx, or Traefik).
5. Verify CORS `BACKEND_CORS_ORIGINS` is locked to legitimate consumer client origins.
