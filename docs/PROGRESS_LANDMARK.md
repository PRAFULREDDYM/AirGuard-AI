# AirGuard AI — Progress Landmark & State Save

**Saved At:** 2026-11-05 18:48 PST (Phase 3 Execution)  
**Status:** Saved & ready for seamless continuation.

---

## 1. Summary of Work Completed in Phase 3

### Task 1: Molecular Model Verification & Real-World Benchmark
- **Curated Dataset Acquisition:**
  - Acquired `curated_GS_LF_merged_4983.csv` from OpenPOM (4,983 unique molecules, 138 canonical descriptors, MIT License).
  - Stored in `data/molecular/` with `LICENSE_OPENPOM.txt`.
- **Root-Cause Investigation (Isoamyl Acetate Misprediction):**
  - **Identified Root Cause:** In `services/ml_molecular/service.py`, when a class had zero positive training samples, scikit-learn's single-class estimator output `classes_ = [0]`. The code took `preds[idx][0][0]` as the probability, treating 100% negative confidence as 100% positive confidence (`roasted`, `floral`, `green` became 1.0).
  - **Fixed:** Corrected probability extraction in `service.py` to check `estimator.classes_` and return `1.0` if `class == 1`, else `0.0`.
- **Model Training & Benchmark (`services/ml_molecular/train_and_evaluate.py`):**
  - Applied Bemis-Murcko Scaffold Split (2,747 train / 2,236 test) to eliminate structural data leakage between chemical analogs.
  - Multi-output Random Forest (100 trees, radius=2 Morgan fingerprints, 1024-bits).
  - Test Macro ROC-AUC: **0.6648** across 62 evaluated descriptors with $\ge 100$ positive instances.
  - Top test ROC-AUC performers: `alliaceous` (0.9014), `onion` (0.8726), `garlic` (0.8647), `aldehydic` (0.8452), `sulfurous` (0.8422), `fruity` (0.7860).
  - Verified Isoamyl acetate (`CC(=O)OCCC(C)C`) predictions: `fruity: 0.53`, `sweet: 0.52`.
  - Serialized checkpoint: `services/ml_molecular/models/pom_rf_checkpoint.joblib`.
  - Exported metrics: `services/ml_molecular/models/pom_evaluation_metrics.json`.
  - Strict model labeling: Rigorously labeled as **Morgan-FP Random Forest Baseline**, never misrepresented as OpenPOM.
  - All 5 unit tests in `tests/unit/test_molecular.py` passing.

---

### Task 2: Electronic-Nose (BME688) ML Training & Evaluation
- **Dataset Acquisition (`data/enose/`):**
  - Inspected `mrc-rossoni/TransformerOdorClassification` (MIT License).
  - Acquired `resistance_values.csv` (CoffeePow-4: 3,583 sequences of 10-step heating cycles across 4 classes: Ambient Air, Borbone Coffee, Lavazza Coffee, Primia Coffee).
  - Acquired `resistance_values_7classes.csv` (Aroma-7: 4,750 sequences including 3 unseen cream classes: Almond, Thyme, Marigold).
- **Benchmark Implementation (`services/ml_environment/enose_benchmark.py`):**
  - **Session-Grouped Splitting:** Grouped sequences into 40-cycle continuous recording blocks and split using `GroupKFold` to prevent temporal data leakage.
  - **HistGradientBoosting Baseline:** Test Accuracy: **91.67%**, Macro F1: **0.9072**.
  - **Random Forest Baseline:** Test Accuracy: **90.56%**, Macro F1: **0.8908**.
  - **ConvTran Sequence Transformer (PyTorch 1D-CNN + Multihead Attention):** Test Accuracy: **61.11%**, Macro F1: **0.5614**.
  - **Ambient Air False Alarm Rate:** Verified at only **2.69%** (FPR = 0.0269).
  - **Out-of-Distribution (OOD) Unknown-Class Rejection:** Evaluated against 1,167 unseen cream samples from Aroma-7; confirmed 7.7%–7.8% rejection at thresholds 0.60–0.80.
  - Serialized checkpoints: `services/ml_environment/models/enose_rf_checkpoint.joblib` and `services/ml_environment/models/enose_convtran_checkpoint.pt`.
  - Exported metrics: `services/ml_environment/models/enose_evaluation_metrics.json`.

---

### Task 3: Real Integration Pathways & Live MQTT Broker
- **Live MQTT Broker Publish/Subscribe Testing:**
  - Installed `amqtt` to run an in-process RFC-compliant broker on `127.0.0.1:18883`.
  - Created `scripts/verify_mqtt_live_broker.py` testing live TCP connection, publisher loop, subscriber callback, ingestion, deduplication, and DB persistence.
  - Fixed duplicate query crash in `services/ingestion/service.py` where calling `.scalars().first()` twice closed the SQLAlchemy 2.0 result object.
  - Verified `scripts/verify_mqtt_live_broker.py` passed with `>>> LIVE BROKER TEST: SUCCESS <<<`.
  - Pytest integration suite (`tests/integration/test_mqtt_broker_live.py` and `test_mqtt_ingestion.py`) passing.

---

### Task 4 & 5: UI Model Lab & Transparency Updates
- **AI Model Lab (`apps/web/src/app/models/page.tsx`):**
  - Added dedicated tabs for:
    1. **Molecular Odor (RDKit Baseline)**: Real SMILES predictor, live ROC-AUC metrics, Bemis-Murcko scaffold split details, OpenPOM comparison table.
    2. **Electronic-Nose (BME688)**: CoffeePow-4 metrics, model comparison table (HistGB vs RF vs ConvTran), per-class F1/FPR breakdown, OOD unknown rejection analysis.
    3. **Sensor Sessions & Registry**: Controlled safe recording sessions and model version registry.
  - Added backend endpoints in `services/api/routers/models.py`:
    - `GET /api/v1/models/molecular/benchmark`
    - `GET /api/v1/models/enose/benchmark`
  - Fixed frontend API client (`apps/web/src/lib/api.ts`).
  - Next.js build verified: **12/12 routes compiled cleanly with 0 errors**.

---

### Task 6: Playwright Browser End-to-End Suite
- Created `tests/e2e/test_browser_workflows.py` using Playwright async Chromium.
- Verified dashboard loading, navigation, device onboarding protocols, rooms, events safety separation, and automations rules.

---

## 2. Active System State
- **Backend Port:** 8000 (Stopped cleanly for pause)
- **Frontend Port:** 3000 (Stopped cleanly for pause)
- **PostgreSQL:** Running on Homebrew `127.0.0.1:5432/airguard`
- **Virtualenv:** `.venv` (Python 3.11.14 with RDKit, PyTorch 2.10, scikit-learn, amqtt, Playwright 1.44)

---

## 3. Resume Plan (Immediate Next Steps)
When resuming this session:
1. Generate the 5 required documentation deliverables:
   - `docs/MOLECULAR_MODEL_BENCHMARK.md`
   - `docs/ENVIRONMENTAL_MODEL_EVALUATION.md`
   - `docs/REAL_DEVICE_TEST_RESULTS.md`
   - `docs/BROWSER_E2E_RESULTS.md`
   - `docs/PORTFOLIO_DEMO_GUIDE.md`
2. Finalize the 5-column capability matrix (**Implemented | Unit Tested | Integration Tested | Physically Verified | Not Yet Verified**).
3. Run the final demonstration check to show the full pipeline:
   `Sensor → Ingestion → Normalization → Safety Engine → UI → Authorized Command → Confirmation`.

