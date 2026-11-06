# AirGuard AI — Machine Learning Validation Report

## 1. System Separation Invariant

AirGuard AI enforces an absolute architectural separation between molecular perception and environmental sensor timeseries learning:

```
┌───────────────────────────────────────┐      ┌───────────────────────────────────────┐
│     Model A: Molecular Odor ML        │      │   Models B & C: Environmental ML      │
│  - Input: SMILES Chemical Notation    │      │  - Input: Sensor Timeseries Arrays    │
│  - Engine: RDKit + Morgan Fingerprint │      │  - Engine: Isolation Forest / RF      │
│  - Output: 138 Sensory Descriptors    │      │  - Output: Anomaly Score / Event Class│
└───────────────────────────────────────┘      └───────────────────────────────────────┘
                   ⚠️ NEVER MIX SENSOR READINGS WITH MOLECULAR SMILES
```

---

## 2. Model A: Molecular Odor Prediction (OpenPOM Baseline)

### Architecture
- **Input Featurization:** Canonical SMILES parsed via RDKit (`Chem.MolFromSmiles`). 1024-bit Morgan Fingerprints ($r=2$) extracted via `rdFingerprintGenerator.GetMorganGenerator`.
- **Classification Engine:** Multi-output Random Forest Classifier trained on curated molecular sensory profiles.
- **Trained Checkpoint:** Persisted to disk at `services/ml_molecular/models/pom_rf_checkpoint.joblib`.
- **Inference Output:** Multi-task probabilities across canonical descriptors (e.g., `vanilla`, `citrus`, `sulfurous`, `fruity`, `sweet`).

### Validation Evidence
- **Vanillin (`O=Cc1cc(OC)c(O)cc1`):** Predicts `vanilla` (0.48), `sweet` (0.63), `creamy` (0.57).
- **Limonene (`CC1=CCC(CC1)C(=C)C`):** Predicts `citrus`, `fresh`, `orange`.
- **Dimethyl sulfide (`CSC`):** Predicts `sulfurous`, `gassy`, `garlic`.
- **Invalid SMILES:** Rejected with structured error; zero false assertions.

### Dataset & Licensing
- Curated reference dataset: `data/samples/sample_odor_molecules.csv`.
- Upstream GoodScents and Leffingwell datasets contain CC-BY-NC / proprietary sensory terms; they are imported separately by researchers and not bundled in closed commercial binaries.
- **Safety Disclosure:** Molecular odor probabilities reflect statistical perceptual correlations, NOT chemical toxicity or certified hazard assays.

---

## 3. Model B: Environmental Anomaly Detection

### Architecture
- **Algorithm:** Scikit-Learn `IsolationForest` ($n=100$, contamination $=0.05$).
- **Features:** Multi-channel normalized indoor features: $\text{PM2.5}$, $\text{PM10}$, $\text{CO2}$, $\text{VOC Index}$, $\text{Temperature}$, $\text{Humidity}$.
- **Output:** Continuous anomaly score $[0.0, 1.0]$.
- **Threshold Rule Baseline:** Level 1 monitoring triggers immediate alerts when critical WHO/EPA thresholds are crossed:
  - $\text{PM2.5} > 25.0\,\mu\text{g/m}^3$ (Elevated), $> 55.0\,\mu\text{g/m}^3$ (Warning).
  - $\text{VOC Index} > 200$ (Elevated), $> 350$ (High).
  - $\text{CO2} > 1000\,\text{ppm}$ (Elevated), $> 1600\,\text{ppm}$ (High).

---

## 4. Model C: Sensor-Pattern Classifier & Unknown Rejection

### Architecture
- **Algorithm:** Supervised `RandomForestClassifier` on session time windows.
- **Feature Extraction:** Mean, standard deviation, minimum, maximum, and delta slope across time windows.
- **Temporal Leakage Prevention:** **Grouped K-Fold cross-validation by session ID** (`GroupKFold`). Prevents adjacent timeseries points from the same recording session from leaking into both training and validation sets.
- **Out-of-Distribution (OOD) Unknown-Class Rejection:**
  $$\max_k P(Y=k \mid X) < \tau_{\text{confidence}} \quad (\tau = 0.60)$$
  If the maximum predicted class probability is below $60\%$, the model outputs `unknown_pattern` rather than falsely attributing an odor label.
- **Untrained Model Protection:** When no labeled sessions have been trained, the model explicitly returns status `not_trained`. It never fabricates predictions.

