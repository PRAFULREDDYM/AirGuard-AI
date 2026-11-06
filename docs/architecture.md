# AirGuard AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  Dashboard │ Rooms │ Devices │ Events │ Automations │ AI Lab    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────┴───────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  Auth │ Homes │ Rooms │ Devices │ Readings │ Events │ Models    │
├─────────────────────────────────────────────────────────────────┤
│                      Service Layer                               │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │Ingestion │ │Automation │ │  Safety  │ │  Notifications   │  │
│  │ Service  │ │  Engine   │ │  Engine  │ │    Service       │  │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│       │             │            │                 │             │
│  ┌────┴─────────────┴────────────┴─────────────────┴─────────┐  │
│  │              Database (PostgreSQL)                         │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Integration Layer                             │
│  ┌────────┐ ┌──────┐ ┌──────────┐ ┌───────┐ ┌──────┐ ┌──────┐ │
│  │  Home  │ │ MQTT │ │AirGradnt │ │ESPHome│ │ REST │ │ Sim  │ │
│  │  Asst  │ │      │ │          │ │       │ │      │ │      │ │
│  └────────┘ └──────┘ └──────────┘ └───────┘ └──────┘ └──────┘ │
├─────────────────────────────────────────────────────────────────┤
│                       ML Layer                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Env Anomaly (B)  │  │ Sensor Class (C) │  │ Molecular (A) │ │
│  │ scikit-learn      │  │ scikit-learn      │  │ OpenPOM       │ │
│  │ Always available  │  │ Needs training   │  │ Isolated env  │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Runtime Architecture

### Single-process MVP (development/local)
- FastAPI serves API + WebSocket
- Background tasks for ingestion polling, automation evaluation
- PostgreSQL via SQLAlchemy async
- Frontend: separate Next.js dev server proxying to API

### Production-ready (future)
- API behind reverse proxy
- Separate ingestion worker(s) for high-volume sensor data
- Redis for pub/sub between services (optional)
- Container orchestration

## Module Boundaries

### API (`services/api/`)
- FastAPI application with routers
- Authentication (JWT)
- CRUD for homes, rooms, devices
- Sensor reading queries
- Event/alert management
- Automation rule management
- Model management endpoints
- WebSocket for live updates

### Integrations (`services/integrations/`)
- `base_adapter.py` — DeviceAdapter protocol
- `home_assistant/` — HA REST + WS adapter
- `mqtt/` — Paho MQTT adapter
- `airgradient/` — AirGradient local API adapter
- `esphome/` — ESPHome REST/SSE adapter
- `rest_generic/` — Generic REST adapter
- `simulation/` — Simulation adapter

### Ingestion (`services/ingestion/`)
- Canonical SensorReading schema
- Unit normalization
- Timestamp validation
- Deduplication
- Staleness detection
- Database persistence
- Real-time broadcast (WebSocket)

### ML Environmental (`services/ml-environment/`)
- Rule-based monitoring (thresholds)
- Anomaly detection (Isolation Forest)
- Sensor-pattern classifier
- Data collection sessions
- Feature extraction
- Model training / evaluation
- Model registry

### ML Molecular (`services/ml-molecular/`)
- OpenPOM integration (isolated)
- CSV dataset inspection
- SMILES validation
- Odor descriptor prediction
- Model versioning

### Automation (`services/automation/`)
- Rule engine (if/then/else)
- Condition evaluation
- Device command dispatch
- Hysteresis / cooldown
- Rate limiting
- Manual override
- Audit logging

### Safety (`services/automation/safety.py`)
- Event classification hierarchy
- Life-safety rules
- Command validation
- Notification decisions

## Data Flow

```
Sensor Device
    │
    ▼
Adapter (poll/subscribe)
    │
    ▼
Ingestion Service
  ├─ Validate & normalize
  ├─ Persist to DB
  ├─ Broadcast via WebSocket
  └─ Forward to ML pipeline
        │
        ▼
    ML Service
      ├─ Anomaly score
      ├─ Classification (if trained)
      └─ Create Event if significant
            │
            ▼
        Safety Engine
          ├─ Classify event severity
          ├─ Check safety constraints
          └─ Trigger notifications
                │
                ▼
            Automation Engine
              ├─ Evaluate rules
              ├─ Check permissions
              ├─ Rate limit
              └─ Send command to adapter
```

## Database Schema (key tables)

- `users` — authentication, profile
- `homes` — user's home(s)
- `rooms` — rooms within a home
- `devices` — connected devices with capabilities
- `device_capabilities` — measurement types, control types per device
- `connections` — adapter credentials (encrypted)
- `sensor_readings` — canonical telemetry (partitioned by time)
- `sensor_calibrations` — calibration records
- `environmental_events` — detected anomalies/classifications
- `alerts` — user-facing notifications
- `automation_rules` — if/then rules
- `automation_executions` — audit log of actions
- `data_collection_sessions` — labeled recording sessions
- `event_labels` — labels for training
- `model_versions` — ML model registry
- `model_evaluations` — metrics per model version
- `audit_logs` — security audit trail

