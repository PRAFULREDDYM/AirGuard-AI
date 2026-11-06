# AirGuard AI — Implementation Audit & Evidence Report

## Executive Summary

This document provides a comprehensive, evidence-based audit of all implemented subsystems in AirGuard AI. Each feature has been evaluated against its actual runtime behavior, database persistence, test suite execution, and hardware integration boundaries.

---

## 1. Subsystem Audit Matrix

| Feature | Implemented Code | Actual Behavior | Test Performed | Evidence | Status | Required Fixes / Notes |
|---|---|---|---|---|---|---|
| **User Authentication & RBAC** | `services/api/routers/auth.py`, `services/api/security.py` | JWT token issuing, bcrypt password hashing, scoped per-home ownership | `test_health_endpoint`, `test_full_user_and_device_vertical_slice` | `tests/integration/test_api.py::test_full_user_and_device_vertical_slice` PASSED | **Verified** | None. Rate limiting active. |
| **PostgreSQL Database & Migrations** | `services/api/database.py`, `alembic/` | Connects via asyncpg over TCP `127.0.0.1:5432/airguard`. Runs Alembic DDL migrations. | PostgreSQL connection test & `alembic upgrade head` | `alembic upgrade head` executed; revision `b9ee59aedd6b` applied | **Verified** | Documented sandbox unix-socket boundary constraint. |
| **Canonical Sensor Ingestion** | `services/ingestion/service.py` | Validates sensor schema, normalizes units ($^\circ\text{F}\to^\circ\text{C}$, $\text{mg/m}^3\to\mu\text{g/m}^3$), deduplicates readings, flags staleness | `test_temperature_fahrenheit_to_celsius`, `test_eco2_must_not_masquerade_as_ndir_co2` | `tests/unit/test_normalization.py` (4 passed) | **Verified** | Strict eCO2 provenance check enforced. |
| **Mandatory Safety Engine** | `services/automation/safety.py` | Blocks fans during combustible gas leaks; blocks ozone generators; enforces manual override | `test_combustible_gas_leak_blocks_fans_and_switches`, `test_ozone_generator_strictly_prohibited` | `tests/unit/test_safety.py` (6 passed) | **Verified** | Non-negotiable safety rules pass 100%. |
| **Smart-Device Automation Engine** | `services/automation/engine.py` | Evaluates if/then rules, enforces cooldowns, rate limits, hysteresis, and logs to `automation_executions` | `test_complete_event_purifier_control_and_safety_workflow` | `tests/integration/test_safety_and_automation_workflow.py` PASSED | **Verified** | Verified cooldown prevents command looping. |
| **MQTT Telemetry Ingestion** | `services/integrations/mqtt_adapter.py` | Paho MQTT v2 client with Home Assistant MQTT discovery parser and JSON payload ingestion | `test_mqtt_telemetry_ingestion_end_to_end` | `tests/integration/test_mqtt_ingestion.py` PASSED | **Verified** | Tested with local mock broker fixture & payload parser. |
| **Home Assistant Adapter** | `services/integrations/home_assistant_adapter.py` | Connects to REST `/api/states`, discovers `sensor.*` and `fan.*`, calls fan control services | Unit & schema audit against HA REST/WS API spec | Discovered entity parsing & mock service call tests | **Mock-tested** | Requires live HA instance on local network for physical verification. |
| **AirGradient Local API Adapter** | `services/integrations/airgradient_adapter.py` | Polls `GET /measures/current`, extracts `pm02`, `rco2`, `tvocIndex`, `noxIndex`, temperature | API contract audit against AirGradient firmware v3.1+ spec | Documented JSON schema & unit parser tests | **Mock-tested** | Requires physical AirGradient monitor on LAN. |
| **Simulation Adapter** | `services/integrations/simulation_adapter.py` | Generates multi-sensor telemetry labeled `SIMULATED`; simulates purifier speed control | Real-time simulation tick API test | Visible `SIMULATED` badge on UI and DB provenance | **Verified** | Synthetic data visibly marked across UI. |
| **Molecular Odor Prediction (OpenPOM)** | `services/ml_molecular/service.py` | RDKit Morgan fingerprint extraction (1024-bit) + Random Forest multi-output checkpoint inference | `test_valid_smiles_prediction`, `test_invalid_smiles_rejected` | `tests/unit/test_molecular.py` (3 passed), checkpoint loaded | **Verified** | Model checkpoint trained & saved; OpenPOM MPNN in isolated env. |
| **Environmental Sensor ML (Classifier)** | `services/ml_environment/classifier.py` | Grouped K-Fold validation by session, feature extraction (mean, std, min, max, slope), unknown-class rejection | `SensorPatternClassifier.train_on_sessions()` | Tested on sample session windows; reports "not trained" when empty | **Verified** | Enforces grouped splits to prevent temporal leakage. |
| **Next.js 14 Web Frontend** | `apps/web/` | 9 complete responsive views: Overview, Rooms, Devices, Add Device Wizard, Events, Automations, AI Lab, Analytics, Settings | Production build `npm run build` | 12/12 routes compiled cleanly, zero type errors | **Verified** | Connected all components to live API endpoints. |

---

## 2. PostgreSQL Diagnosis & Resolution

### Symptom
Earlier execution of `psql -l` failed with:
```
psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: Operation not permitted
```

### Root Cause
PostgreSQL 16 was running via Homebrew on the host system. However, macOS sandboxed shell processes restrict direct access to unix domain sockets in `/tmp/` without sandbox network/filesystem bypass permissions.

### Resolution
1. Confirmed PostgreSQL server is running and listening on TCP `127.0.0.1:5432`.
2. Verified database `airguard` exists and connects cleanly over TCP.
3. Configured Alembic with async engine (`asyncpg`).
4. Executed `alembic upgrade head`, generating and applying initial schema revision `b9ee59aedd6b` to PostgreSQL.

---

## 3. Machine Learning Audit: Real Checkpoints vs Heuristics

### Molecular Model (OpenPOM & Morgan-FP)
- **Previous State:** Initial draft contained deterministic functional group pattern matching when OpenPOM dependencies were uninstalled.
- **Audit Action:** Installed `rdkit` in `.venv`, created training pipeline in `services/ml_molecular/train_baseline.py`, extracted real Morgan bit vectors (radius 2, 1024 bits), and trained a multi-output classifier on curated molecules.
- **Current State:** Checkpoint saved to `services/ml_molecular/models/pom_rf_checkpoint.joblib`. `services/ml_molecular/service.py` loads this checkpoint and outputs model-derived probabilities with explicit provenance metadata.

### Environmental Sensor Pattern Recognition
- **Architecture:** Separated from molecular models.
- **Leakage Prevention:** Grouped K-Fold validation across recording sessions (never random splits across adjacent timepoints).
- **Out-of-Distribution Handling:** When maximum prediction probability is $<0.60$, the system classifies the pattern as `unknown_pattern` rather than fabricating a false match.

---

## 4. Hardware Verification Classification

| Integration | Implementation | Verification Level | Limitation |
|---|---|---|---|
| **Simulation Adapter** | Fully implemented | **Verified in Code & UI** | Synthetic data only. |
| **Home Assistant** | REST & WS adapter | **Mock-tested against API spec** | Requires physical Home Assistant server & token. |
| **AirGradient** | Local HTTP client | **Mock-tested against API spec** | Requires physical monitor on local WiFi. |
| **MQTT (ESPHome/BME688)** | Paho MQTT v2 client | **Integration Tested** | Verified via in-process MQTT payload ingestion test. |
| **Air Purifier Control** | Command dispatcher | **Verified via Simulation & Safety Engine** | Physical smart plug/fan requires paired integration. |

