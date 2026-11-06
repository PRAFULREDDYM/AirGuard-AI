# AirGuard AI — Implementation Plan

## Milestone Sequence

### M0: Repository Setup & Audit ✅
- [x] Read PRD
- [x] Research OpenPOM, odor-model-pipeline, IoT APIs
- [x] License audit
- [x] Create project structure
- [x] Create AGENTS.md
- [x] Create agent skills
- [x] Create architecture docs

### M1: First Vertical Slice (Current)
**Goal:** Working frontend + backend + database + basic monitoring

Backend:
- [ ] FastAPI application with health check
- [ ] PostgreSQL database setup + Alembic migrations
- [ ] User authentication (JWT)
- [ ] Home/Room/Device CRUD
- [ ] Sensor reading ingestion endpoint
- [ ] Simulation adapter generating labeled synthetic data
- [ ] WebSocket for live updates
- [ ] Basic event detection (threshold-based)

Frontend:
- [ ] Next.js app with routing
- [ ] Login/registration
- [ ] Overview dashboard
- [ ] Room detail page
- [ ] Device list with status
- [ ] Real-time sensor charts
- [ ] Light/dark mode
- [ ] Responsive layout

### M2: Real Device Integrations
- [ ] Home Assistant adapter (REST + WebSocket)
- [ ] MQTT adapter (paho-mqtt)
- [ ] AirGradient local API adapter
- [ ] Device pairing wizard UI
- [ ] Connection health monitoring
- [ ] Capability discovery

### M3: Environmental Intelligence
- [ ] Data quality validation pipeline
- [ ] Staleness detection
- [ ] Anomaly detection (Isolation Forest)
- [ ] Event logging and timeline
- [ ] Alert notifications
- [ ] Events UI page

### M4: ML Pipelines
- [ ] Molecular odor prediction (OpenPOM, isolated)
- [ ] Random Forest baseline on Morgan fingerprints
- [ ] Data collection session recording
- [ ] Session labeling UI
- [ ] Sensor-pattern classifier training
- [ ] Model registry and versioning
- [ ] AI Model Lab UI

### M5: Safe Automation
- [ ] Rule engine with conditions
- [ ] Device command dispatch
- [ ] Cooldown/hysteresis
- [ ] Manual override
- [ ] Safety constraints
- [ ] Audit logging
- [ ] Automation builder UI

### M6: Testing & Validation
- [ ] Unit tests (pytest)
- [ ] Integration tests with mock servers
- [ ] E2E tests (Playwright)
- [ ] Security testing
- [ ] Accessibility audit

### M7: Polish & Documentation
- [ ] Complete README with setup instructions
- [ ] Model cards
- [ ] Troubleshooting guide
- [ ] Environment file examples
- [ ] Docker Compose configuration
- [ ] Release checklist

