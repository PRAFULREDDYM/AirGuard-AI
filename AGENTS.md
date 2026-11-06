# AirGuard AI — Engineering Constraints & Safety Rules

## Product Identity

AirGuard AI is an AI-powered environmental air-quality monitoring, odor-pattern recognition, and smart-device automation application. It connects to real sensors and devices via Home Assistant, MQTT, AirGradient, ESPHome, and REST APIs.

## Non-Negotiable Safety Rules

1. **Never equate a bad smell with a confirmed toxic hazard.** Odor descriptors are statistical predictions, not chemical assays.
2. **Never equate the absence of a detected smell with safety.** Many dangerous gases are odorless.
3. **Never infer CO from VOC, PM2.5, or estimated CO2.** CO detection requires a dedicated electrochemical sensor.
4. **Preserve certified detector alarms independently of ML output.** Smoke/CO alarms are life-safety systems.
5. **Never activate fans or electrical switches for suspected combustible-gas leaks.** Electrical activation can cause ignition.
6. **Never activate ozone generators.** Ozone is a respiratory irritant.
7. **Never disable alarms or override certified safety systems.**
8. **Never claim medical-grade or certified safety monitoring.**
9. **Always show uncertainty and missing data.** Never present missing readings as zero or safe.
10. **Never present simulated data as real measurements.** Simulation must always be visually labeled.

## Data Integrity Rules

- **Raw vs. derived:** Always track whether a value is a direct sensor measurement or a derived/estimated quantity.
- **eCO2 ≠ NDIR CO2:** Estimated CO2 from VOC sensors must never be labeled as direct CO2 measurement.
- **VOC index ≠ gas concentration:** Sensirion/Bosch VOC indices are relative, not absolute ppm.
- **Missing ≠ zero:** A missing reading means the sensor is unavailable, not that the value is zero.
- **Stale readings:** Readings older than the configured freshness window must be flagged.
- **Calibration status:** Track warm-up periods and calibration quality per sensor.

## ML Model Rules

- **Molecular models (OpenPOM):** Accept SMILES strings only. Never feed PM2.5/VOC/temperature data into a molecular model.
- **Environmental models:** Accept sensor timeseries only. Separate anomaly detection from classification.
- **Untrained models:** Must report "not trained" — never fabricate predictions.
- **Model promotion:** No model auto-promotes to production. Requires explicit user approval after evaluation.
- **Training data:** Never create hazardous chemical exposures for training data collection.
- **Leakage prevention:** Use session-grouped splits, not random splits on adjacent observations.

## Device Control Rules

- Only execute commands the device actually supports (verified via capability manifest).
- Respect manual overrides — never silently re-enable automation over a user override.
- Rate-limit commands (max 1 per device per 30s default).
- Log all control actions to the audit trail.
- Life-safety events → warn and guide, never automate fans/HVAC.
- Commands must be idempotent where possible.

## Architecture Conventions

- **Python backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL.
- **Frontend:** Next.js 14+, React, TypeScript strict mode, Tailwind CSS, shadcn/ui, Recharts.
- **Integrations:** Capability-based adapter pattern. Every adapter implements the `DeviceAdapter` interface.
- **ML environments:** OpenPOM/RDKit/DeepChem in an isolated virtual environment. Core app must work without them.
- **Testing:** pytest for Python, Playwright for E2E, Jest for frontend unit tests.
- **Secrets:** Never commit tokens/passwords. Use `.env` files (gitignored) and env vars.
- **Error handling:** All API endpoints return structured error responses. No raw exceptions to clients.

## Code Style

- Python: Black formatting, isort imports, type hints everywhere, Pydantic models for all API contracts.
- TypeScript: ESLint + Prettier, strict null checks, no `any` types in production code.
- SQL: Alembic migrations for all schema changes. Never raw SQL in application code (use SQLAlchemy).
- Git: Conventional commits. Feature branches. Tests must pass before merge.

