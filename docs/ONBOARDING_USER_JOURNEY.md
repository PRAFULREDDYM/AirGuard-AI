# AirGuard AI — Onboarding User Journey Specification

## Overview

The AirGuard AI onboarding flow (`/onboarding`) guides consumers through an 8-stage setup sequence that bridges physical hardware, local network discovery, room assignments, privacy consent, and dual operating modes (**Monitor & Notify** vs. **Automatic Purifier Control**).

---

## 8-Stage Onboarding Architecture

```
[ Stage 1: Welcome & Safety Limits ]
                 │
                 ▼
[ Stage 2: Connect Devices (HA / Direct / Sensor) ]
                 │
                 ▼
[ Stage 3: Live Verification & Handshake ]
                 │
                 ▼
[ Stage 4: Assign Rooms & Sensor-Purifier Pairings ]
                 │
                 ▼
[ Stage 5: Select Operating Mode ]
        ├── Monitor & Notify (Default)
        └── Automatic Purifier Control
                 │
                 ▼
[ Stage 6: Permissions & Unbundled Consent ]
                 │
                 ▼
[ Stage 7: System Dry-Run & Guarded Test Pulse ]
                 │
                 ▼
[ Stage 8: Activate, Summary & Dashboard Redirection ]
```

---

## Stage-by-Stage Breakdown

### Stage 1: Welcome & Product Limits
- **Purpose**: Establishes transparent safety boundaries and operating expectations prior to any hardware or telemetry interaction.
- **Key Disclaimers**:
  - AirGuard AI is **not a certified replacement** for certified smoke alarms, carbon monoxide detectors, or combustible gas sensors.
  - Odor and VOC classifications are statistical machine-learning predictions, not chemical assays.
  - AirGuard supports **Local-First Operation**: credentials and sensor streams are kept on the local network whenever possible without mandatory cloud telemetry.
- **User Actions**:
  - Review disclaimers.
  - Advance to Stage 2 via "Begin Setup".

### Stage 2: Connect Devices
- **Purpose**: Unified selection and connection of physical or simulated hardware across Home Assistant, direct local REST/WebSocket, and AirGradient/ESPHome/MQTT sensors.
- **Supported Integration Categories**:
  1. **Existing Smart Home Platform**: Home Assistant WebSocket/REST API with long-lived access token.
  2. **Dedicated Air Quality Monitors**: AirGradient ONE, AirGradient Open Air, Awair Element, Qingping.
  3. **Smart Air Purifiers**: Levoit (Core 400S, 300S), Coway Airmega (via HA or local mock), Xiaomi Smart Air Purifier.
  4. **Custom Sensors & Gateway**: ESPHome / BME688 electronic nose with warmup guard.
- **Handling Unsupported Devices**: Explicitly directs users to supported alternatives or Home Assistant bridging rather than failing silently.

### Stage 3: Verify Connections
- **Purpose**: Distinguishes between successful authentication/handshake and physical hardware telemetry receipt.
- **Verification Criteria**:
  - Live socket ping / latency (<150ms).
  - Fresh sensor payload receipt (PM2.5, VOC, Temperature, Relative Humidity).
  - Actuator handshake (verifying fan speed / power state query).
- **Visual Status**:
  - `VERIFIED_LIVE` (green pill with latency).
  - `AUTHENTICATED_WAITING_TELEMETRY` (amber pill).
  - `CONNECTION_FAILED` (red pill with retry actionable error).

### Stage 4: Assign Rooms & Sensor-Purifier Pairing
- **Purpose**: Physical spatial modeling. Associates air quality monitors directly with smart air purifiers residing in the same physical room.
- **Spatial Safety Constraint**:
  - Purifiers can **only** be automatically controlled by sensors physically located in the same room. Cross-room cross-talk is prevented.

### Stage 5: Select Operating Mode
- **Dual Mode Choice**:
  1. **Monitor & Notify (Default / Recommended)**:
     - Real-time air quality metrics, interactive charts, and anomaly notifications.
     - Zero automatic device control or fan speed modifications.
     - Ideal for users desiring passive environmental awareness.
  2. **Automatic Purifier Control**:
     - Includes all monitoring and alerting capabilities.
     - Grants explicitly authorized, rule-bound automatic control of verified purifiers.
     - Strictly restricted to particulate filtration (PM2.5 / PM10) — never actuated by unvalidated odor or VOC spikes.

### Stage 6: Permissions & Unbundled Consent
- **Purpose**: Fine-grained, legally compliant consent management (GDPR/CCPA compliant).
- **Unbundled Permissions**:
  - `TELEMETRY_ACCESS`: Read and store sensor measurements.
  - `PUSH_NOTIFICATIONS`: Deliver alerts and threshold warnings.
  - `DEVICE_CONTROL`: Send actuation commands to verified purifiers (mandatory for Mode 2, disabled for Mode 1).
  - `CLOUD_PROCESSING`: Optional off-premises telemetry backup.
  - `AI_TRAINING_SHARE`: Strictly opt-in sharing of anonymized sensor recordings for ML calibration.
- **Reversibility**: Consents can be revoked at any time from `/settings`.

### Stage 7: Test & Dry-Run
- **Purpose**: End-to-end operational dry-run before activating production automations.
- **Interactive Tests**:
  - **Sensor Reception Test**: Pings active monitor and checks data freshness (<30s).
  - **Notification Dispatch**: Dispatches a test alert to the in-app notification center.
  - **Guarded Purifier Pulse**: Brief 3-second fan pulse verifying physical actuator response, requiring explicit user click confirmation.

### Stage 8: Review & Activation
- **Purpose**: Final state persistence and transition to room dashboard.
- **Activation Payload**:
  - Commits `operating_mode`, `consents`, `room_assignments`, and `notification_preferences` to database.
  - Redirects to `/rooms` or dashboard.
  - Informs the user of the global navbar **"Pause All Automations"** kill-switch.

---

## State Persistence & Navigation Flow
- Users can step back to previous stages without losing entered credentials.
- In-flight states are held in local state and validated server-side on stage submission.
