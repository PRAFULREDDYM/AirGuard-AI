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

