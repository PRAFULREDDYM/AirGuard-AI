# AirGuard AI — License Audit

## Code Dependencies

| Component | License | Commercial Use | Notes |
|-----------|---------|---------------|-------|
| **OpenPOM** | MIT | ✅ Yes | Pip-installable, full reuse allowed |
| **odor-model-pipeline** | ❌ No license | ⛔ Cannot use | No license = all rights reserved. DO NOT incorporate code. |
| **FastAPI** | MIT | ✅ Yes | |
| **Pydantic** | MIT | ✅ Yes | |
| **SQLAlchemy** | MIT | ✅ Yes | |
| **Next.js** | MIT | ✅ Yes | |
| **React** | MIT | ✅ Yes | |
| **Tailwind CSS** | MIT | ✅ Yes | |
| **shadcn/ui** | MIT | ✅ Yes | |
| **Recharts** | MIT | ✅ Yes | |
| **PyTorch** | BSD-3 | ✅ Yes | |
| **scikit-learn** | BSD-3 | ✅ Yes | |
| **RDKit** | BSD-3 | ✅ Yes | |
| **DeepChem** | MIT | ✅ Yes | |
| **DGL** | Apache 2.0 | ✅ Yes | |
| **paho-mqtt** | EPL 2.0 / EDL 1.0 | ✅ Yes | |
| **PostgreSQL** | PostgreSQL License | ✅ Yes | |

## Datasets

| Dataset | Source | License | Commercial Use | Action |
|---------|--------|---------|---------------|--------|
| curated_GS_LF_merged_4983.csv | GoodScents + Leffingwell | Mixed ⚠️ | Restricted | See below |
| curated_GS_LF_merged_4984.csv | GoodScents + Leffingwell | Mixed ⚠️ | Restricted | See below |
| Leffingwell PMP | CC-BY-NC | ❌ Non-commercial only | Research/educational use only |
| GoodScents | Proprietary/Copyright | ❌ Restricted | Requires explicit permission |

### Dataset Decision

> [!WARNING]
> The curated GS-LF merged datasets contain data from Leffingwell (CC-BY-NC) and GoodScents
> (proprietary). These datasets can be used for research and educational purposes but
> **cannot be included in a commercial product distribution** without explicit licensing.

**Implementation approach:**
1. The application provides infrastructure for importing and using odor datasets
2. CSV files are NOT bundled in the repository
3. Users download datasets separately and import them via the UI
4. Documentation explains provenance and licensing restrictions
5. A sample dataset with freely-licensed molecules can be provided for testing

## Firmware / Sensor Libraries

| Component | License | Can Bundle? | Notes |
|-----------|---------|-------------|-------|
| **BSEC Library** (Bosch) | Proprietary, hardware-bound | ❌ No | Only for Bosch sensors, cannot redistribute binaries |
| **BME68x SensorAPI** (Bosch) | BSD-3 | ✅ Yes | Raw sensor driver, no AI/BSEC features |
| **ESPHome** | MIT/GPL mix | Reference only | Use API, don't bundle source |
| **Home Assistant** | Apache 2.0 | Reference only | Use API, don't bundle source |
| **BME AI-Studio** | Proprietary | ❌ No | Desktop app, cannot redistribute |

### Firmware Decision

> [!IMPORTANT]
> - Use ESPHome and Home Assistant through their documented APIs only
> - Do NOT clone or bundle their source code
> - BSEC library cannot be distributed — document as optional user-installed component
> - Provide firmware configuration *examples* only, not complete firmware distributions

## Actions Required

1. ✅ Use OpenPOM (MIT) for molecular odor prediction
2. ⛔ Do NOT use odor-model-pipeline code (no license)
3. ⚠️ Do NOT bundle GS-LF CSV datasets — provide import infrastructure
4. ⛔ Do NOT bundle BSEC binaries — document as optional
5. ✅ Use all other dependencies (all permissively licensed)
6. ✅ Build our own Random Forest baseline using scikit-learn (independent implementation)
7. ✅ Reference ESPHome/HA through APIs only

