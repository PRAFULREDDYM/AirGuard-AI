# AirGuard AI — Product Requirements Document

**Version:** 1.0  
**Product type:** AI-powered environmental sensing, air-quality intelligence and smart-device automation  
**Platforms:** Responsive web application/PWA, local gateway, optional cloud services  
**Primary users:** Homeowners, renters, smart-home enthusiasts, indoor-air-quality researchers and building operators

## 1. Product vision

Build an intelligent environmental monitoring system that receives real measurements from compatible air purifiers, air-quality monitors, smart-home devices and dedicated environmental sensors.

The application analyzes those measurements to recognize air-quality changes, identify validated patterns associated with different odor sources, notify users about possible concerns and control compatible devices when doing so is appropriate and safe.

It combines:

1. Real-time environmental monitoring.
2. AI-based sensor-pattern recognition.
3. Molecular odor prediction using OpenPOM.
4. Data collection and custom model training.
5. Smart-home integration and automation.
6. Multi-room dashboards and notifications.
7. Sensor diagnostics, uncertainty reporting and historical analytics.

**Product principle:** Never claim a chemical, odor or danger has been positively identified unless the connected sensing system and its validation support that claim.

## 2. Primary use cases

### UC-01: Automatic air purification

A connected PM2.5 monitor detects increased particle levels during cooking.

The application:
- Records the measurements.
- Identifies an air-quality event.
- Shows the affected room.
- Increases the speed of a compatible purifier if the user enabled automation.
- Monitors whether the readings improve.
- Returns to normal operation after an appropriate cooldown.

### UC-02: Unknown odor-source anomaly

A compatible electronic-nose sensor produces an unusual gas-response pattern.

The application:
- Compares the pattern against a calibrated baseline.
- Determines whether it resembles a validated, trained event class.
- Displays a possible source only if confidence and validation requirements are met.
- Otherwise reports an unidentified anomaly.
- Records the event and notifies the user according to their preferences.

### UC-03: Cleaning-product event

A sensor reports increased VOC activity while someone is cleaning.

The application identifies elevated VOC-related readings. If a separately validated sensor-pattern classifier recognizes the event, it may label the event as possibly cleaning-related.

It recommends appropriate ventilation or source control without asserting that a particular chemical is present.

### UC-04: Certified alarm integration

A compatible certified smoke, CO or other safety alarm reports an alarm event.

The application:
- Clearly identifies the alarm's source.
- Immediately surfaces the alarm.
- Sends configured notifications.
- Shows the relevant emergency guidance.
- Does not treat the ML model as confirmation or dismissal of the alarm.
- Does not issue potentially unsafe fan, HVAC or electrical commands in response to suspected combustible-gas or fire emergencies.

Certified alarms must operate independently of this application.

### UC-05: Custom odor-recognition training

A researcher connects a compatible electronic-nose sensor.

They can:
- Collect environmental sensor sessions.
- Label safe, controlled odor-source examples.
- Export datasets.
- Train and evaluate a classifier.
- Compare model versions.
- Deploy an approved model.
- Revert to an earlier model.

## 3. Product operating modes

### Mode A — Monitoring only

Available when supported devices provide basic air-quality measurements.

Features:
- Live PM2.5, PM10, VOC indices, CO2, temperature and humidity, depending on available sensors.
- Air-quality trends.
- Device health.
- Threshold-based alerts.
- Historical analysis.

No unsupported odor classification.

### Mode B — Anomaly detection

Requires compatible sensor data and sufficient baseline observations.

Features:
- Changes from calibrated normal conditions.
- Statistical anomaly scores.
- Event clustering.
- Confidence and uncertainty indicators.
- Unknown-event handling.

### Mode C — Trained odor-source recognition

Requires a compatible electronic-nose sensor and a separately trained and evaluated classifier.

Features:
- Supported odor-source classes.
- Model version and training provenance.
- Confidence reporting.
- Unknown-class rejection.
- Model performance information.

Classifications represent validated patterns, not guaranteed identification of specific chemical substances.

### Mode D — Automation

Requires explicitly authorized device-control capabilities.

Features:
- User-defined rules.
- Fan-speed control.
- Device on/off where supported.
- Room-based automation.
- Scheduling.
- Manual overrides.
- Action history.
- Command acknowledgment.

Life-safety events must follow a separate safety policy.

## 4. Device connectivity

### Required integration types

**Home Assistant**
- Read available sensor entities.
- Discover supported controllable entities.
- Subscribe to state changes.
- Issue authorized service/action calls.
- Handle authentication, reconnection and permission failures.

**MQTT**
- Connect authenticated brokers.
- Subscribe to sensor telemetry.
- Normalize payloads.
- Publish permitted device commands.
- Handle duplicate, delayed and retained messages.

**ESPHome**
- Integrate compatible environmental-sensor nodes.
- Support BME688 and other supported sensors.
- Preserve measurement provenance.
- Surface calibration and device-health information.

**AirGradient**
- Implement the documented local API.
- Discover or configure supported monitors.
- Retrieve available measurements.
- Preserve measurement names, units and timestamps.

**Generic REST / Webhook**
- Support user-configured documented APIs.
- Require explicit field mapping.
- Validate authentication and data schema.
- Restrict outbound network access to permitted destinations.

**CSV imports**
- Import historical sensor measurements.
- Validate timestamps, units and columns.
- Preview mappings and invalid records.
- Keep imported measurements separate from live telemetry.

**Simulation adapter**
- Generate explicitly labeled synthetic data.
- Demonstrate sensor events and automation without hardware.
- Never present simulated readings as real environmental observations.

### Device capability system

Every device must expose a capability manifest describing:

- Manufacturer, model and firmware version when known.
- Connection protocol.
- Readable measurements and their units.
- Whether values are raw, measured, estimated or derived.
- Supported control operations.
- Polling and streaming capabilities.
- Calibration status.
- Signal freshness.
- Authentication requirements.
- Room assignment.
- Connection quality.
- Command acknowledgment support.

Do not assume all purifiers expose VOC sensors, particle sensors or external APIs.

A passive air filter without electronics must not appear as a connected measurement source.

### Connectivity UI

Implement a device-connection wizard:

1. Select provider or protocol.
2. Show prerequisites and permissions.
3. Enter secure connection information.
4. Test connection.
5. Discover devices.
6. Preview available measurements and controls.
7. Select devices and assign rooms.
8. Configure monitoring preferences.
9. Configure optional automation.
10. Confirm successful data reception.

Provide per-device actions for reconnect, disconnect, rename, edit configuration, recalibrate where applicable, and view diagnostic logs.

## 5. Machine-learning requirements

### Model A: Molecular odor model

Sources:
- https://github.com/biomachinelearning/openpom
- https://github.com/ARY2260/odor-model-pipeline

Inputs:
- Valid molecular SMILES strings.

Outputs:
- Predicted odor descriptors.
- Model scores.
- Version and provenance.

Requirements:
- Inspect the two curated CSV datasets.
- Validate column schema and descriptor labels.
- Identify duplicates and overlapping molecules.
- Review licenses and upstream dataset rights.
- Reproduce an appropriate baseline training pipeline.
- Evaluate with molecular-identity/group-aware splits.
- Support pretrained inference when permitted.
- Isolate dependency versions in a dedicated ML environment.
- Document limitations.

This model must not accept ordinary purifier telemetry as though it were molecular structure data.

### Model B: Environmental anomaly detector

Inputs may include:
- Gas resistance or validated sensor-array channels.
- VOC index.
- NOx index.
- PM1 / PM2.5 / PM10.
- Temperature and humidity.
- CO2 when directly measured.
- Time-window features.
- Validated environmental context.

Requirements:
- Normalize sensor-specific units.
- Handle missing values.
- Reject invalid and stale readings.
- Support per-room baselines.
- Include configurable warm-up and calibration periods.
- Train a simple baseline before advanced architectures.
- Compare statistical rules with Isolation Forest or suitable alternatives.
- Report anomaly scores and model limitations.

### Model C: Sensor-pattern classifier

Use separately collected, labeled electronic-nose data.

Initial safe training classes:
- Baseline indoor air.
- Cooking-related events.
- Coffee.
- Food aromas.
- Cleaning-related events recorded under ordinary safe use.
- Other controlled benign odor sources.
- Mixed/unknown events.

Requirements:
- Separate acquisition sessions and metadata.
- Track sensor model and firmware.
- Track room/site and environmental conditions.
- Store label source and verification level.
- Avoid training/testing leakage across adjacent time windows.
- Evaluate unseen sessions, devices and locations.
- Measure precision, recall, false alarms and missed events.
- Add unknown/out-of-distribution rejection.
- Calibrate probability estimates.
- Track changes in accuracy due to drift.
- Support rollback.

Do not create hazardous chemical exposures to collect training data.

Chemical-specific hazard identification requires suitable target-specific sensing, reference measurements and validation beyond descriptive odor classification.

### Model registry

Track:
- Model ID.
- Model version.
- Training date.
- Dataset identifiers.
- Supported sensor families.
- Preprocessing configuration.
- Training metrics.
- Validation metrics.
- Known limitations.
- Approval status.
- Deployment and rollback history.

A trained model must not be automatically promoted to production solely because training completed.

### Model training UI

Provide:
- Dataset upload and inspection.
- Session labeling.
- Data-quality report.
- Training configuration.
- Training progress.
- Evaluation report.
- Confusion matrix.
- Per-class metrics.
- Version comparison.
- Model deployment and rollback.

## 6. Safety and risk engine

Separate odor classification from risk assessment.

### Information classifications

- **Normal:** Measurements within supported monitoring limits.
- **Elevated reading:** A measured or derived signal exceeds a configured, documented threshold.
- **Unusual pattern:** An anomaly detector has found a change.
- **Possible source:** A validated classifier recognizes a learned pattern.
- **Unknown:** The system cannot reliably classify the event.
- **Certified alarm:** A compatible independent detector has activated.
- **Sensor unavailable:** Measurements cannot support a reliable assessment.

### Mandatory safety rules

- Never equate a bad smell with a confirmed toxic hazard.
- Never equate no detected smell with safety.
- Never infer CO from VOC, PM2.5 or estimated CO2.
- Preserve certified detector alarms independently of ML output.
- Never suggest that ordinary HEPA filtration removes all gases.
- Never activate fans or electrical switches for suspected combustible-gas leaks.
- Never disable alarms or override certified safety systems.
- Never activate ozone generators.
- Never claim a medical or safety certification that has not been obtained.
- Always show uncertainty and missing data.
- Make dangerous-condition notifications distinguishable from ordinary air-quality tips.

Professional safety assessment and applicable regulatory review are required before marketing the product as a hazard-detection system.

## 7. Automation engine

Support a rule model with:

- Trigger source.
- Device or room scope.
- Measurement and threshold.
- Data validity prerequisites.
- Duration and hysteresis.
- Allowed actions.
- User authorization.
- Cooldown.
- Manual override.
- Failure and retry policy.
- Notification policy.
- Audit trail.

Example:

IF validated PM2.5 readings remain elevated for the configured duration AND a compatible purifier is available AND the user has enabled automation, THEN increase purifier fan speed.

Return to normal only after readings are sufficiently improved and the cooldown requirements are satisfied.

### Required controls

- Prevent automation loops.
- Rate-limit device commands.
- Verify device responses when possible.
- Handle disconnected devices.
- Make repeated commands idempotent.
- Respect manual overrides.
- Avoid changing safety-critical equipment.
- Keep local rules functional without cloud connectivity whenever supported.

## 8. User interface

Create a modern, responsive and accessible dashboard.

### Screen 1: Overview

Show:
- Current monitoring status.
- Room overview.
- Recent measurements.
- Connected devices.
- Latest alerts.
- Active automations.
- Sensor-health warnings.

### Screen 2: Room details

Show:
- Room name and assigned sensors.
- Available live measurements.
- Time-series charts.
- Recent events.
- Odor-source classification only when supported.
- Current device states.
- Recommended actions.

### Screen 3: Devices

Show:
- Device cards.
- Connection health.
- Sensor capabilities.
- Control capabilities.
- Firmware version.
- Last successful reading.
- Battery or signal status where available.

### Screen 4: Add device

Provide the full connection wizard specified in Section 4.

### Screen 5: Events and alerts

Show:
- Chronological events.
- Severity and evidence.
- Source device.
- Event duration.
- Model version.
- Notifications and automation actions.
- Event acknowledgment.
- User feedback.

### Screen 6: Automations

Provide a visual rule builder with:
- Room selection.
- Measurement and condition.
- Action selection.
- Test/simulation.
- Enabled/disabled state.
- Recent execution history.

### Screen 7: AI Model Lab

Provide training, dataset, evaluation and model-management workflows.

### Screen 8: Historical analytics

Provide:
- Measurements over time.
- Room comparisons.
- Event frequencies.
- Time in elevated conditions.
- Device responses.
- Before/after event analysis without making unsupported causal claims.
- CSV export.

### Screen 9: Settings and privacy

Provide:
- User profile.
- Home and room management.
- Permissions.
- Notification preferences.
- Data retention.
- Export/delete data.
- Integration credentials management.
- Diagnostics.

### Visual requirements

- Clean, professional UI.
- Consistent component library.
- Responsive desktop, tablet and mobile layouts.
- Light/dark themes.
- Clear warning hierarchy.
- Accessible labels and contrast.
- Loading, empty, disconnected, uncalibrated and error states.
- No fake live readings in production mode.

## 9. Suggested system architecture

### Frontend
- Next.js / React.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- Recharts or another suitable charting library.
- Accessible UI primitives.

### Backend
- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.
- PostgreSQL.
- WebSockets for live updates.

### Device services
- Home Assistant adapter.
- MQTT adapter.
- AirGradient adapter.
- ESPHome integration.
- Generic provider interface.
- Simulation adapter.

### Machine learning
- OpenPOM in an isolated optional environment.
- RDKit and DeepChem where needed.
- PyTorch for compatible molecular models.
- scikit-learn for environmental baselines.
- Model registry and evaluation services.

### Deployment
- Docker Compose for local development.
- Local gateway for home-network discovery and control.
- Optional hosted frontend/backend when justified.
- Documented secure remote-access design.

Keep sensor acquisition, ML inference, risk policies and device control as separate modules.

## 10. Data architecture

Required entities:
- User.
- Home.
- Room.
- Device.
- DeviceCapability.
- SensorReading.
- SensorCalibration.
- Connection.
- EnvironmentalEvent.
- Alert.
- Notification.
- AutomationRule.
- AutomationExecution.
- Dataset.
- DataCollectionSession.
- EventLabel.
- ModelVersion.
- ModelEvaluation.
- AuditLog.

Every reading must retain:
- UTC timestamp.
- Device ID.
- Measurement type.
- Value.
- Unit.
- Sensor source.
- Raw/derived status.
- Quality and calibration status.
- Ingestion time.

Prevent duplicate records, normalize units and account for clock drift.

## 11. Security and privacy

- Strong authentication and authorization.
- Home/user ownership checks.
- Secure integration-token storage.
- Encryption in transit and for sensitive stored credentials.
- No default public exposure of local device services.
- Scoped network access.
- Input validation.
- API rate limiting.
- Command authorization.
- Audit logging.
- Safe error handling.
- Data export and deletion.
- Configurable retention.
- Opt-in diagnostics and telemetry.
- Secret scanning and dependency vulnerability scanning.

Do not expose local network credentials or device tokens to the browser unnecessarily.

## 12. Reliability requirements

The system must:
- Recover from temporary sensor disconnections.
- Detect stale readings.
- Handle malformed and delayed payloads.
- Resume device streams after service restarts.
- Avoid duplicate control commands.
- Preserve user settings.
- Log failed control actions.
- Avoid presenting missing data as zero.
- Report when a model is untrained or unavailable.
- Display appropriate service health.

Set measurable response-time and availability targets after hardware and deployment requirements are established.

## 13. Testing strategy

### Unit tests
- Data normalization.
- Device capability checks.
- Model input validation.
- Automation conditions.
- Safety policies.
- API authorization.

### Integration tests
- Home Assistant connection.
- MQTT messages.
- Sensor ingestion.
- Database persistence.
- Alerts.
- Device commands.

### ML tests
- Data leakage.
- Dataset deduplication.
- Held-out evaluation.
- Missing-data handling.
- Calibration drift.
- Out-of-distribution examples.
- Model version compatibility.

### End-to-end tests
- New-user onboarding.
- Device pairing.
- Live dashboard.
- Alert generation.
- Automation execution.
- Disconnection and reconnection.
- Model-training workflow.
- Data export and deletion.

### Hardware tests
- Real device readings.
- Independent reference measurements where appropriate.
- Sensor warm-up.
- Interference and environmental changes.
- Multiple rooms.
- Real-world operating conditions.

Never use dangerous gas generation as a casual application test.

## 14. Development milestones

### M0 — Repository and feasibility audit
Review source repositories, datasets, licenses, SDKs, hardware capabilities and dependencies.

### M1 — Working connected application
Build frontend, backend, database, authentication, monitoring dashboard and functional simulation mode.

### M2 — Real device connections
Implement Home Assistant, MQTT and one independently tested real air-quality monitor integration.

### M3 — Environmental intelligence
Implement data-quality checks, anomaly detection, event logging and uncertainty reporting.

### M4 — Odor training
Integrate OpenPOM separately, reproduce a molecular baseline and build the labeled sensor-training pipeline.

### M5 — Safe automation
Implement the rule engine, authorized device controls, notifications and safety constraints.

### M6 — Validation
Test real environments, compare models, address false positives, measure reliability and document limitations.

### M7 — Release readiness
Complete deployment instructions, security review, accessibility checks, user documentation and release checklist.

## 15. MVP definition of done

The MVP is complete only when:

1. A user can run the application locally using documented commands.
2. The frontend connects to a functioning backend and database.
3. A user can create a home and rooms.
4. A user can connect at least one supported real sensor integration.
5. The system receives and stores real measurements.
6. The dashboard updates using real received data.
7. A user can see sensor health and calibration status.
8. An anomaly can be detected and recorded.
9. The app can issue a properly labeled alert.
10. A compatible purifier can be controlled through an authorized integration.
11. Rules respect cooldowns and manual overrides.
12. The molecular training pipeline works independently.
13. The sensor training interface accepts valid, labeled sensor recordings.
14. Untrained classifiers do not produce fictional odor identifications.
15. Safety-critical conditions do not trigger unsafe automations.
16. Automated tests cover the main user journeys.
17. Demo data is visibly marked as simulated.
18. Setup, limitations and known unsupported capabilities are documented.

## 16. Explicit exclusions from MVP

Do not claim:
- Universal compatibility with every purifier.
- Guaranteed detection of all dangerous gases.
- Exact chemical identification from generic TVOC readings.
- Medical-grade or certified safety monitoring.
- Reliable mold identification solely from odor patterns.
- Commercial readiness without additional validation and legal review.

## 17. Future enhancements

- Multi-location management.
- Matter-compatible device integrations where supported.
- Bluetooth integrations.
- Additional manufacturer adapters.
- Advanced electronic-nose sensor arrays.
- On-device edge classification.
- Sensor calibration workflows.
- Filter-maintenance recommendations.
- Outdoor versus indoor air-quality comparisons.
- Advanced analytics for buildings.
- Mobile applications.
- Research-grade dataset management.
- Optional cloud synchronization.
- Validated chemical-specific monitoring modules.