# AirGuard AI — Browser End-to-End (E2E) Test Results

**Document Version:** 2.0.0  
**Test Framework:** Playwright 1.44 (Python Async API)  
**Browser Engine:** Chromium (Headless)  
**Test Suite:** `tests/e2e/test_browser_workflows.py`  
**Execution Date:** November 2026  
**Environment:** Next.js 14 Frontend (`http://localhost:3000`), FastAPI Backend (`http://127.0.0.1:8000`)

---

## 1. Executive Summary

A comprehensive automated browser test suite was executed against the live, unified AirGuard AI web application and backend. The suite tested user authentication, live navigation, device onboarding protocols, safety separation callouts, real-time chemical SMILES featurization, electronic-nose model registry views, and input error handling.

**Overall Test Result:** **ALL 7 BROWSER WORKFLOW TESTS PASSED (100% SUCCESS RATE)**  
**Visual Verification Artifact:** `docs/model_lab_verified_e2e.png`

---

## 2. Detailed Workflow Execution Results

### 2.1 Workflow 1: Dashboard & Authentication Flow
- **URL Tested:** `http://localhost:3000/`
- **Actions:** Loaded dashboard, tested automatic demo JWT token acquisition and persistence in browser `localStorage`.
- **Observed Header:** `"Environmental Overview"`
- **Verified Elements:** Air quality score card, active rooms summary, live sensor telemetry indicators, and simulated data provenance disclaimer.
- **Result:** **PASS**

### 2.2 Workflow 2: Connected Devices & Onboarding Wizard
- **URL Tested:** `http://localhost:3000/devices` and `http://localhost:3000/devices/add`
- **Actions:** Navigated to device catalog, opened device connection wizard.
- **Verified Elements:** Protocol cards for all 4 supported integration channels:
  - **Home Assistant** (REST API / Bearer Token)
  - **MQTT** (Broker Host, Port, Discovery)
  - **AirGradient** (Local Server IP, Port 80)
  - **Simulation** (Virtual Multi-Room Scenario)
- **Result:** **PASS**

### 2.3 Workflow 3: Room Management
- **URL Tested:** `http://localhost:3000/rooms`
- **Actions:** Loaded room inventory, validated room hierarchy (Living Room, Kitchen, Sensor Lab).
- **Verified Elements:** Air quality thresholds, device count per room, and room detail link routing.
- **Result:** **PASS**

### 2.4 Workflow 4: Environmental Events & Safety Separation
- **URL Tested:** `http://localhost:3000/events`
- **Actions:** Inspected event audit log.
- **Verified Elements:** Strict visual and semantic separation between:
  - Statistical Odor Classifications (e.g. coffee brewing, cooking saute)
  - Unsupervised Environmental Anomalies
  - Certified Safety Alarm Events (Smoke/CO alarms)
- **Result:** **PASS**

### 2.5 Workflow 5: Automations & Safety Engine Callout
- **URL Tested:** `http://localhost:3000/automations`
- **Actions:** Loaded automation rules registry.
- **Verified Elements:** Non-negotiable safety rules callout explicitly displayed:
  - *"Never activate fans or switches during suspected combustible-gas leaks (ignition hazard)."*
  - *"Ozone generators strictly prohibited."*
  - *"Certified life-safety alarms override software automation."*
- **Result:** **PASS**

### 2.6 Workflow 6: AI Model Lab (Molecular & E-Nose Benchmarks)
- **URL Tested:** `http://localhost:3000/models`
- **Actions:**
  1. Filled SMILES input field with Isoamyl acetate: `CC(=O)OCCC(C)C`.
  2. Clicked `"Predict Odors"`.
  3. Verified live RDKit featurization and multi-output Random Forest inference.
  4. Asserted predicted descriptors include **`fruity`** (53%) and **`sweet`** (52%).
  5. Clicked **Electronic-Nose (BME688)** tab.
  6. Verified benchmark table displaying HistGradientBoosting (91.67% acc), Random Forest (90.56% acc), ConvTran Transformer (61.11% acc), and Ambient Air FPR (2.69%).
- **Result:** **PASS**

### 2.7 Workflow 7: Input Validation & Error Handling
- **URL Tested:** `http://localhost:3000/models`
- **Actions:** Entered invalid chemical string: `INVALID_SMILES_CHEMICAL_XYZ###` and submitted.
- **Observed Behavior:** Backend rejected request with structured 400 Bad Request error: *"Invalid SMILES string: RDKit failed to parse molecule structure."*
- **UI Behavior:** Clean error badge rendered without React unhandled exception or page crash.
- **Result:** **PASS**

---

## 3. Playwright Execution Console Output

```
--- 1. Testing Dashboard and Auto-Login ---
Page title: AirGuard AI — Environmental Sensing & Odor Intelligence
Dashboard header: Environmental Overview

--- 2. Testing Devices Onboarding ---
Verified protocol cards: Home Assistant, MQTT, AirGradient, Simulation.

--- 3. Testing Rooms Page ---
Rooms page loaded successfully.

--- 4. Testing Events History & Hazard Separation ---
Events page rendered with safety policy separation.

--- 5. Testing Automations & Safety Engine Callout ---
Automations page rendered with non-negotiable safety rules callout.

--- 6. Testing AI Model Lab (Molecular & E-Nose) ---
Live SMILES prediction verified: Isoamyl acetate predicted fruity/sweet successfully.
Electronic-Nose benchmark tab verified with genuine BME688 metrics.

--- 7. Testing Invalid SMILES Rejection ---
Invalid chemical structure rejected with structured error message.
Captured E2E verification screenshot: docs/model_lab_verified_e2e.png

>>> ALL PLAYWRIGHT E2E BROWSER TESTS PASSED <<<
```

---

## 4. Visual Evidence Artifact

The screenshot below was automatically captured during the headless Playwright session:
- **File:** `docs/model_lab_verified_e2e.png`
- **Contents:** Verified live AI Model Lab interface showing SMILES prediction results, model provenance callouts, and the electronic-nose benchmark dashboard.

