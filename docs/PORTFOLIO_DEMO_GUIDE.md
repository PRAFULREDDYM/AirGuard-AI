# AirGuard AI — Portfolio & Demonstration Guide

**Project Name:** AirGuard AI — Environmental Sensing, Odor Intelligence & Automation  
**Repository Architecture:** Full-Stack Monorepo (FastAPI + Next.js 14 + PostgreSQL/SQLite + PyTorch + RDKit)  
**Safety & Compliance:** Strict Non-Negotiable Safety Policy (Combustible gas & ozone generator prohibitions)

---

## 1. Executive Summary

**AirGuard AI** is a production-grade, AI-powered environmental monitoring, electronic-nose odor recognition, and smart-device automation platform. Unlike superficial air-quality dashboards, AirGuard AI integrates real hardware protocols (MQTT, Home Assistant, AirGradient Local API), implements rigorous machine learning with data-leakage prevention, strictly separates statistical odor predictions from chemical hazard detection, and enforces life-safety automation constraints.

### Core Value Pillars
1. **Multi-Protocol IoT Integration:** Connects to physical monitors and smart air purifiers via Home Assistant REST API, MQTT (ESPHome/BME688), and AirGradient Local API with zero cloud dependencies.
2. **Dual-Pillar Machine Learning:**
   - **Molecular Odor Mapping:** Predicts sensory descriptors directly from chemical structures (SMILES) using Morgan circular fingerprints and Bemis-Murcko scaffold splits over 4,983 validated molecules.
   - **Electronic-Nose Pattern Recognition:** Classifies transient MOS gas sensor resistance sequences from Bosch BME688 10-step temperature cycles (CoffeePow-4: 91.67% accuracy; Aroma-7).
3. **Mandatory Safety Engine:** Hardcoded rules block fan or switch actuation during suspected combustible gas leaks, prohibit ozone generators, and guarantee manual user override supremacy.
4. **Data Integrity:** Strict mathematical separation between measured NDIR CO2 and VOC-estimated eCO2; explicit labeling of simulated data; automated sensor drift tracking and staleness detection.

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                       Next.js 14 Client (TypeScript)                   │
│  Dashboard • Device Pairing • AI Model Lab • Automations • Analytics   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP / WebSocket
┌────────────────────────────────────▼───────────────────────────────────┐
│                      FastAPI Backend Core (Python 3.11)                │
│  Auth (JWT) • Device Registry • REST API • Live WebSocket Broadcaster  │
└───────┬────────────────────────────┬───────────────────────────┬───────┘
        │                            │                           │
┌───────▼──────────────┐   ┌─────────▼───────────────┐   ┌───────▼───────┐
│  Ingestion Service   │   │  Safety Policy Engine   │   │  ML Services  │
│  - Unit Normalization│   │  - Combustible Gas Ban  │   │  - Molecular  │
│  - Deduplication     │   │  - Ozone Generator Ban  │   │  - E-Nose     │
│  - Freshness Tracking│   │  - Manual Override Lock │   │  - Anomaly    │
└───────┬──────────────┘   └─────────┬───────────────┘   └───────┬───────┘
        │                            │                           │
┌───────▼────────────────────────────▼───────────────────────────▼───────┐
│              PostgreSQL 16 / SQLite Database (SQLAlchemy 2.0)          │
│   Homes • Rooms • Devices • Sensor Readings • Events • Audit Trail     │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │
┌────────────────────────────────────┴───────────────────────────────────┐
│                     Device Connectivity Adapters                       │
│     MQTT (amqtt/paho) • Home Assistant REST • AirGradient Local API    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Quickstart & Local Execution Commands

### 3.1 Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 16 (optional; defaults to SQLite `sqlite+aiosqlite:///./airguard.db` for zero-friction local execution)

### 3.2 Environment Setup
```bash
# 1. Clone repository and enter directory
cd "AirGuard AI"

# 2. Set up Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
pip install -r services/ml_molecular/requirements.txt
pip install -r services/ml_environment/requirements.txt
pip install amqtt pytest-playwright
playwright install chromium

# 3. Set up Frontend dependencies
cd apps/web && npm install && cd ../..

# 4. Initialize Database Schema
PYTHONPATH=. .venv/bin/alembic upgrade head
```

### 3.3 Running the Services
In two separate terminal windows:

**Terminal 1 — FastAPI Backend:**
```bash
source .venv/bin/activate
PYTHONPATH=. python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Documentation available at: `http://127.0.0.1:8000/docs`*

**Terminal 2 — Next.js Frontend:**
```bash
cd apps/web
npm run dev -- -p 3000
```
*Web Application available at: `http://localhost:3000`*

---

## 4. Verification & Testing Commands

| Verification Target | Command | Expected Output |
|---|---|---|
| **Full Unit & Integration Suite** | `PYTHONPATH=. .venv/bin/python -m pytest tests/unit/ tests/integration/` | **20 passed** |
| **Live MQTT Broker Loop** | `PYTHONPATH=. .venv/bin/python scripts/verify_mqtt_live_broker.py` | `>>> LIVE BROKER TEST: SUCCESS <<<` |
| **Complete Closed-Loop Pipeline** | `PYTHONPATH=. .venv/bin/python scripts/verify_complete_pipeline.py` | `>>> COMPLETE PIPELINE VERIFIED SUCCESSFULLY <<<` |
| **Playwright Browser E2E Suite** | `PYTHONPATH=. .venv/bin/python tests/e2e/test_browser_workflows.py` | `>>> ALL PLAYWRIGHT E2E BROWSER TESTS PASSED <<<` |
| **Molecular ML Training & Benchmark** | `PYTHONPATH=. .venv/bin/python services/ml_molecular/train_and_evaluate.py` | Macro ROC-AUC: **0.6648** on 62 descriptors |
| **E-Nose BME688 Model Benchmark** | `PYTHONPATH=. .venv/bin/python services/ml_environment/enose_benchmark.py` | HistGB: **91.67%**, RF: **90.56%**, FPR: **2.69%** |

---

## 5. Live Demonstration: Closed-Loop Execution Path

To demonstrate the full working pipeline from sensor reading to authorized device actuation:

```
[Simulated Sensor / Hardware Node]
  │
  ├─► 1. Sensor Ingestion:
  │      Device transmits PM2.5 = 65.0 µg/m³ (Unhealthy threshold exceeded).
  │
  ├─► 2. Ingestion Service:
  │      Normalizes units, verifies sensor freshness, and confirms data provenance (MEASURED).
  │
  ├─► 3. AI / Anomaly Engine:
  │      Dynamic Z-Score detects anomaly (Z = +3.82); classifies pattern as benign cooking exhaust.
  │
  ├─► 4. Safety Policy Engine:
  │      Evaluates rule conditions:
  │      - Combustible gas detected? NO (Safe).
  │      - Target device is ozone generator? NO (Permitted).
  │      - Manual override active? NO (Automated actuation permitted).
  │
  ├─► 5. Purifier Control Dispatched:
  │      Sends `set_percentage(100)` command to Living Room Air Purifier via adapter.
  │
  ├─► 6. Audit Trail & WebSocket:
  │      Action recorded in `audit_logs` table and broadcast live to the web dashboard.
```

Run this demonstration anytime with:
```bash
PYTHONPATH=. .venv/bin/python scripts/verify_complete_pipeline.py
```

---

## 6. Comprehensive 5-Column Capability Matrix

This matrix documents the verification state of all application capabilities in strict compliance with the project's evidence rules:

| Functional Capability | Implemented | Unit Tested | Integration Tested | Physically Verified | Not Yet Verified |
|---|:---:|:---:|:---:|:---:|:---:|
| **REST API & JWT Authentication** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **PostgreSQL Schema & Alembic Migrations** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Unit Normalization & Deduplication** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **eCO2 vs. Direct NDIR CO2 Separation** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Sensor Freshness & Drift Detection** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Mandatory Safety Engine (Gas/Ozone bans)** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Manual User Override Lockout** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Morgan-FP Molecular Odor Baseline** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Bemis-Murcko Scaffold Leakage Prevention**| ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **OpenPOM Comparison Framework** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **BME688 Electronic-Nose Classifier** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Session-Grouped Cross-Validation** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Out-of-Distribution Unknown Rejection** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **MQTT Adapter (Telemetry & Subscriptions)** | ✅ Yes | ✅ Yes | ✅ Yes (amqtt) | ❌ No | ⚠️ Awaiting Hardware |
| **Home Assistant REST Adapter** | ✅ Yes | ✅ Yes | ✅ Yes (Spec) | ❌ No | ⚠️ Awaiting Hardware |
| **AirGradient Local API Adapter** | ✅ Yes | ✅ Yes | ✅ Yes (Spec) | ❌ No | ⚠️ Awaiting Hardware |
| **Simulated Multi-Room Sensor Adapter** | ✅ Yes | ✅ Yes | ✅ Yes | — | N/A (Simulation) |
| **Next.js 14 Responsive Web Dashboard** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |
| **Playwright Automated E2E Browser Suite** | ✅ Yes | ✅ Yes | ✅ Yes | — | — |

