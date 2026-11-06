# AirGuard AI — Device Connection Security Audit & Protections (Phase 7)

## 1. Threat Model & Security Posture

Connecting smart IoT hardware, local discovery gateways, and third-party smart-home platforms introduces distinct security attack vectors. Phase 7 implements defense-in-depth mitigations across the connection lifecycle.

---

## 2. Implemented Security Controls

### 2.1 Server-Side Request Forgery (SSRF) Defense
- **Vulnerability:** The device discovery gateway accepts target IP addresses and ports to probe local devices prior to pairing (`POST /api/v1/gateway/probe`). Without validation, an attacker could force the server to probe cloud metadata services (e.g. `http://169.254.169.254/latest/meta-data/`), internal databases, or arbitrary public IP addresses.
- **Mitigation:**
  1. Strict IP parsing using Python's `ipaddress.ip_address`.
  2. Immediate rejection of link-local metadata addresses (`169.254.0.0/16`), multicast (`224.0.0.0/4`), and reserved addresses.
  3. Rejection of public WAN IP ranges (probing restricted to RFC 1918 private subnets: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, and loopback `127.0.0.1`).
  4. Strict Port Whitelisting: Probes are permitted ONLY on documented IoT device ports:
     - `80` (HTTP local devices / AirGradient / Awair)
     - `8080` (Alternative HTTP web servers)
     - `8123` (Home Assistant REST / WebSocket)
     - `9926` (AirGradient alternate port)
     - `6053` (ESPHome native API)
     - `1883` / `8883` (MQTT & Secure MQTTS)
     - `8000` (Local testing loopback)

### 2.2 Cross-Home Insecure Direct Object Reference (IDOR) Isolation
- **Vulnerability:** Multi-tenant smart home applications risk cross-account tampering if device endpoints (`/devices/{id}/command`, `/devices/{id}/authorization`, `/devices/{id}/manual-override`, `/devices/{id}/disconnect`) query devices purely by UUID without checking ownership.
- **Mitigation:**
  - Implemented `get_user_device(db, device_id, current_user.id)` across all device routers.
  - Queries `Device` joined with `Home` where `Home.owner_id == current_user.id`.
  - Rejects cross-home requests with `403 Forbidden` if the device belongs to another user's home, and `404 Not Found` if the device does not exist.
  - Formally verified in integration suite (`tests/integration/test_phase7_consumer_connectivity.py::test_cross_home_idor_isolation`).

### 2.3 At-Rest Credential Encryption
- **Requirement:** Manufacturer cloud tokens, Home Assistant long-lived access tokens, and Wi-Fi pre-shared keys must never be stored in plaintext.
- **Mitigation:**
  - AES-256-GCM symmetric authenticated encryption.
  - Unique initialization vector (IV) generated per credential block.
  - Master key managed via environment variables (`AIRGUARD_SECRET_KEY`) and never committed to version control.
  - Passwords and tokens masked in API responses and frontend views.

### 2.4 Device Lifecycle Audit Trail
- Every critical security action generates an immutable audit record in the `audit_logs` table:
  - `DEVICE_PAIRED`: When a new device is registered and capabilities verified.
  - `DEVICE_COMMAND`: When an actuation command is executed, including parameter values, caller identity, and physical execution result.
  - `DEVICE_DISCONNECTED`: When a device is manually or automatically taken offline.
  - `SAFETY_VIOLATION_BLOCKED`: When the Safety Engine suppresses a command due to fire/gas emergency or missing authorization.

---

## 3. Security Verification Checklist

| Security Requirement | Status | Verification Evidence |
| :--- | :--- | :--- |
| **SSRF Link-Local Metadata Blocked** | **VERIFIED** | `POST /gateway/probe` with `169.254.169.254` returns `400 Bad Request` |
| **SSRF Non-IoT Port Blocked** | **VERIFIED** | `POST /gateway/probe` on port 22/25 returns `400 Bad Request` |
| **Cross-Home IDOR Blocked** | **VERIFIED** | Attacker User B commanding User A device returns `403 Forbidden` |
| **Credential Encryption at Rest** | **VERIFIED** | AES-256-GCM cipher string persisted in database |
| **Immutable Audit Logging** | **VERIFIED** | All command dispatches and disconnects logged to `AuditLog` |
| **Rate-Limiting on Actuation** | **VERIFIED** | 30-second cooldown enforced between device commands |
