# AirGuard AI 🍃

> **AI-Powered Environmental Air-Quality Monitoring, Odor-Pattern Recognition, and Safe Smart-Device Automation.**

AirGuard AI connects real environmental air-quality monitors, electronic-nose sensor arrays, and smart-home purifiers. It receives authentic telemetry, detects unusual environmental anomalies, supports training custom classifiers on user-labeled sensor sessions, predicts sensory odor descriptors from molecular structures using OpenPOM, and safely controls air purifiers with strict hazard exclusions.

---

## 🛡️ Non-Negotiable Safety Rules

1. **Bad smell ≠ Confirmed toxic hazard:** Odor descriptors are statistical pattern predictions, not chemical assays.
2. **Absence of smell ≠ Safety:** Many hazardous gases (such as Carbon Monoxide) are odorless.
3. **Never infer CO from VOC or PM2.5:** Carbon monoxide requires dedicated electrochemical sensors.
4. **Certified alarms remain independent:** Certified smoke/CO alarms are life-safety systems.
5. **Combustible gas leaks strictly block electrical switching:** Actuating fans or switches during suspected combustible-gas leaks introduces ignition risks.
6. **Ozone generators are prohibited:** Ozone is a severe respiratory irritant.
7. **Simulated data is always unmistakably labeled:** Simulated test telemetry is never presented as authentic physical observations.
8. **Missing data is never zero:** Unavailable sensors display as unavailable, not safe or zero.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js 14 Frontend                        │
│  Overview │ Rooms │ Devices │ Events │ Automations │ AI Lab     │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────┴───────────────────────────────────────┐
│                     FastAPI Backend Gateway                     │
│  Auth │ Ingestion │ Automation │ Safety Engine │ Model Registry │
├─────────────────────────────────────────────────────────────────┤
│                   Hardware Integration Layer                    │
│  Home Assistant │ MQTT │ AirGradient │ ESPHome │ Simulation     │
├─────────────────────────────────────────────────────────────────┤
│                        Machine Learning                         │
│  - Level 1: Rule-Based Environmental Monitoring                 │
│  - Level 2: Isolation Forest Anomaly Detection                  │
│  - Level 3: Grouped K-Fold Sensor Classifier (OOD Rejection)    │
│  - Molecular: OpenPOM / Morgan-FP SMILES Odor Mapping           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+ & npm**
- Optional: PostgreSQL 16 (SQLite used automatically for zero-friction local execution)

### 1. Clone & Set Up Python Virtual Environment
```bash
cd "AirGuard AI"
python3.11 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
```

### 2. Start Backend API Server
```bash
# In Terminal 1:
export PYTHONPATH="."
./.venv/bin/uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 3. Start Next.js Frontend
```bash
# In Terminal 2:
cd apps/web
npm run dev
```
Open your browser at: `http://localhost:3000`

### 4. Instant Demo Mode
Click **"Demo Login"** or log in with:
- **Email:** `demo@airguard.ai`
- **Password:** `airguard123`

The demo environment immediately seeds:
- A multi-room smart residence (Living Room, Kitchen, Bedroom)
- Simulated AirGradient ONE particulate monitor
- Simulated Controllable HEPA Air Purifier
- Live simulated telemetry stream with interactive scenario testing (Normal, Cooking PM2.5 spike, Cleaning VOC spike)

---

## 📦 Consumer Beta Installation & Packaging (Phase 8)

AirGuard AI provides a zero-terminal, consumer-friendly macOS Beta installer. Ordinary users do not need to manage virtual environments, Python paths, Docker containers, or terminal windows.

```bash
# 1. Run the standalone macOS installer:
./scripts/install_macos.sh

# 2. Control & inspect background services:
airguard-ctl doctor     # Runs full pre-flight health & port diagnostics
airguard-ctl status     # Shows launchd daemon PID, API status, and database info
airguard-ctl logs       # Streams live background service logs
airguard-ctl restart    # Gracefully restarts local gateway

# 3. Clean uninstallation:
./scripts/uninstall_macos.sh
# To uninstall and purge all data:
./scripts/uninstall_macos.sh --purge-data
```

### 📋 Phase 8 Readiness & Verification Matrix

For complete transparency, every hardware pathway and platform subsystem is evaluated against rigorous validation tiers:

| Subsystem / Feature | Implementation Status | Verification Level | Notes |
| :--- | :--- | :--- | :--- |
| **macOS Beta Installer & launchd Agent** | Implemented | **Physically Verified** | User-space launchd agent, sleep/wake resilience, desktop launcher |
| **Atomic Pre-Dispatch Safety Recheck** | Implemented | **Physically Verified** | Blocks commands if consent revoked or pause toggled during evaluation |
| **Home Assistant Integration** | Implemented | **Provider-Tested** | Tested against official HA REST/WS API contracts & mock server |
| **AirGradient Local API (`/measures/current`)**| Implemented | **Provider-Tested** | Tested against official v1 local endpoint schema |
| **SafePurifier HEPA (Simulation)** | Implemented | **Physically Verified** | Full software closed-loop physics emulation |
| **Direct Device Adapter (miIO/REST)** | Implemented | **Mock-Tested** | Tested with simulated local protocol payloads |
| **Dyson / Tuya / Cloud-Only Purifiers** | Flagged / Guidance | **Blocked** | Cloud-dependent or proprietary tokens; bridged via HA |
| **In-App Notification Center** | Implemented | **Physically Verified** | Read tracking, quiet hours suppression, cooldown deduplication |
| **Web Push API Subscriptions & Delivery ACK** | Implemented | **Physically Verified** | Endpoints store keys; ACK transitions status to DELIVERED |
| **Device-Offline Health Scanner** | Implemented | **Physically Verified** | Detects stale telemetry (>300s) and deduplicates offline alerts |
| **Alembic Database Migrations (`c8f1e31d45ab`)** | Implemented | **Physically Verified** | Zero-loss schema upgrades tested on populated databases |
| **SSRF & Network Gateway Protection** | Implemented | **Physically Verified** | Blocks cloud metadata (`169.254.169.254`) and non-IoT ports |
| **Production Mock & Demo Isolation** | Implemented | **Physically Verified** | Rejects demo login and unmounts mock routes in production |
| **Environmental Sensor Odor Classifier** | Research Prototype | **51.62% Acc (Holdout)** | **NOT reliable for household odor identification**; fan control prohibited |
| **Molecular Odor Prediction (OpenPOM)** | Implemented | **Provider-Tested** | Accepts SMILES only; strictly decoupled from sensor streams |

---

## 🔌 Hardware Connectivity & Consumer Onboarding (Phase 7 & 8)

AirGuard AI provides a consumer-friendly, zero-configuration device pairing and onboarding experience (`/onboarding`) that eliminates terminal commands, manual YAML configuration, and raw IP address entry for ordinary home users.

### 🌟 Dual Operating Modes
1. **Mode 1: Monitor & Notify (Default / Recommended):**
   - Connect compatible sensors, display live readings/history/quality, and deliver in-app & push notifications.
   - Zero automatic device control or fan speed modification.
   - Read the [Monitor & Notify Specification](docs/MONITOR_NOTIFY_SPEC.md).
2. **Mode 2: Automatic Purifier Control:**
   - Includes all monitoring and alerting capabilities.
   - Explicitly authorized, rule-bound automatic control of verified purifiers.
   - **Particulate-Only Invariant:** Purifier speed increases are strictly tied to particulate filtration (PM2.5 / PM10); actuation is never triggered by unvalidated odor or VOC spikes.
   - Read the [Automatic Purifier Control Specification](docs/AUTOMATIC_PURIFIER_CONTROL_SPEC.md).

### 🧭 8-Stage Guided Onboarding Journey (`/onboarding`)
- **Stage 1 (Welcome & Limits):** Transparent product limits, local-first operation, and life-safety alarm independence.
- **Stage 2 (Connect Devices):** Brand/model selection across Home Assistant, direct local REST, and AirGradient monitors.
- **Stage 3 (Verify Connections):** Live socket ping, telemetry freshness check, and actuator response verification.
- **Stage 4 (Assign Rooms):** Explicit physical mapping of monitors to purifiers in the same room.
- **Stage 5 (Select Mode):** Clear choice between Monitor & Notify and Automatic Purifier Control.
- **Stage 6 (Permissions & Consent):** Unbundled, versioned, and revocable consent matrix.
- **Stage 7 (Test & Dry-Run):** Interactive sensor ping, notification test dispatch, and user-confirmed guarded fan pulse.
- **Stage 8 (Review & Activation):** Final state persistence and transition to room dashboard.
- Read the full [Onboarding User Journey Guide](docs/ONBOARDING_USER_JOURNEY.md).

### 🛑 Emergency Global Kill-Switch & 14 Safety Invariants
- **Global Pause Button:** A persistent "Pause All Automations" kill switch is accessible from the top navigation bar. Clicking it halts all automation evaluations across all rooms instantaneously (`home.automations_paused == True`).
- **14 Server-Side Invariants:** Enforced via `SafetyEngine.validate_automation_action` (conservative emergency suspension on fire/gas hazard, manual override hold, 120s sensor freshness window, room matching, and particulate-only automation).
- Read the [Automation Safety Invariants Specification](docs/AUTOMATION_SAFETY_INVARIANTS.md).

### 🔐 Privacy, GDPR & Consent Management
- **Unbundled Permissions:** Telemetry access, notifications, device control, and AI training data sharing are decoupled and independently revocable.
- **Revocation Cascade:** Revoking `DEVICE_CONTROL` in `/settings` server-side blocks all future automated actuations.
- **Data Subject Rights:** Full account JSON export (`GET /api/v1/auth/export-data`) and permanent account data deletion (`DELETE /api/v1/auth/delete-account-data`).
- Read the [Consent & Permissions Matrix](docs/CONSENT_PERMISSION_MATRIX.md) and [E2E Test Results](docs/ONBOARDING_E2E_RESULTS.md).

### 🎯 Three Operational Capability Tiers
AirGuard strictly surfaces device capabilities across three unambiguous tiers:
- **Tier 1 (Basic Actuation & Control):** Controllable smart purifiers (Levoit Core 200S/300S/400S/600S, Xiaomi Smart Air Purifier 4/Pro/Compact, Coway, Philips, IKEA Starkvind). Discrete fan speeds, modes, and safe automated clean-air throttling.
- **Tier 2 (Air-Quality Monitoring):** Laser particulate monitors (AirGradient ONE, Awair Element, PurpleAir). Direct NDIR CO2, PM2.5, PM10, Sensirion SGP41 TVOC & NOx indices.
- **Tier 3 (Advanced Odor-Pattern Recognition):** Multi-gas heated MOX sensor arrays (AirGuard Sensor Node / BME688 10-step temperature-ramped resistance). **Hardware lacking MOX gas sensors is explicitly flagged as "Tier 3 Odor AI Not Available on this hardware"**; odor predictions are never fabricated from standard particulate readings.

### 🛡️ Conservative Emergency Suspended State (`EMERGENCY_SUSPENDED`)
Unlike naive smart home scripts that attempt to switch electrical fans or relays "OFF" during fire or gas leaks (which risks contact spark ignition in explosive gas mixtures or disrupts certified building smoke evacuation systems), AirGuard enters **`EMERGENCY_SUSPENDED`**:
- Halts all automated switching immediately.
- Leaves electrical relays untouched to prevent contact arcing.
- Alerts the user with prominent emergency evacuation guidance.

### 🔒 Gateway Security & Cross-Home IDOR Defense
- **Strict SSRF Protection:** Gateway discovery rejects cloud metadata (`169.254.169.254`), public WAN IP ranges, and restricts probing exclusively to whitelisted IoT ports (`80, 8080, 8123, 9926, 6053, 1883, 8883, 8000`).
- **Cross-Home Isolation:** Multi-tenant device endpoints enforce home ownership validation (`Home.owner_id == current_user.id`), rejecting cross-account tampering with `403 Forbidden`.
- **At-Rest Encryption:** Manufacturer credentials and tokens are encrypted with AES-256-GCM before storage.

---

## 🔌 Hardware Connectivity Guide

### 1. Home Assistant
- Go to **Devices → Connect New Device → Home Assistant**
- Provide your instance URL (e.g., `http://homeassistant.local:8123`) and a **Long-Lived Access Token** (generated under your HA Profile).
- AirGuard AI discovers environmental sensors (`sensor.pm25`, `sensor.temperature`, `sensor.co2`) and controllable fans (`fan.air_purifier`).
- Credentials are encrypted at rest with AES-256-GCM.

### 2. AirGradient Local API
- Connect any **AirGradient ONE (v3.0.10+ firmware)** monitor on your local network.
- Go to **Devices → Connect New Device → AirGradient Local API**.
- Enter device IP (e.g., `192.168.1.150`). AirGuard directly queries `GET /measures/current` for direct PM2.5, PM10, direct NDIR CO2 (`rco2`), and Sensirion SGP41 TVOC/NOx indices.

### 3. MQTT Broker
- AirGuard subscribes to `homeassistant/sensor/#` and custom `airguard/#` topics.
- Auto-parses Home Assistant MQTT Discovery configs and maps sensor telemetry.

---

## 🧪 AI Model Lab

### Molecular Odor Prediction (OpenPOM)
- Navigate to **AI Model Lab → Molecular Odor (OpenPOM)**.
- Input any valid SMILES chemical structure (e.g., `O=Cc1cc(OC)c(O)cc1` for Vanillin or `CC(=O)OCCC(C)C` for Isoamyl acetate).
- Predicts sensory perception probabilities across the 138 canonical odor descriptors.
- *Strict Rule:* Molecular models accept SMILES only. Telemetry is never routed to molecular models.

### Environmental Sensor Pattern Recognition
- Navigate to **AI Model Lab → Environmental Sensor ML**.
- Collect and label safe, controlled indoor events (e.g. coffee brewing, saute cooking, clean ambient air).
- Train classifiers using **Grouped K-Fold validation** across sessions to eliminate time-adjacent data leakage.
- Enforces **unknown-class rejection** when pattern confidence falls below threshold.

---

## ⚡ Smart-Device Automations & Safety

- Navigate to **Automations** to create rule-based actions (e.g., `IF PM2.5 > 35 µg/m³ THEN set Purifier speed to high`).
- **Cooldowns & Hysteresis:** Configurable minimum intervals prevent rapid oscillation and command flooding.
- **Manual Overrides:** Users can engage manual override at any time; automated rules are immediately suspended.
- **Audit Log:** Every command execution and safety intervention is recorded in the immutable audit trail.

---

## 🧪 Automated Testing

Run the automated test suite:
```bash
export PYTHONPATH="."
./.venv/bin/python -m pytest tests/
```

Test coverage includes:
- `tests/unit/test_safety.py`: Mandatory safety rules & combustible gas fan blocks
- `tests/unit/test_normalization.py`: Unit normalization & eCO2 provenance enforcement
- `tests/unit/test_molecular.py`: SMILES validation & odor descriptor prediction
- `tests/integration/test_api.py`: End-to-end user onboarding, device pairing, telemetry ingestion, anomaly detection, and automated actuation

---

## 📜 Licenses & Upstream Data Attribution

- **OpenPOM Code:** Licensed under the MIT License.
- **Odor Sensory Data:** Curated GoodScents and Leffingwell datasets carry non-commercial research licensing. AirGuard provides modular import infrastructure without packaging restricted data.
- **Bosch BSEC / AI-Studio:** Proprietary Bosch software. AirGuard supports raw sensor telemetry and standard APIs; closed-source BSEC binaries are not distributed.

