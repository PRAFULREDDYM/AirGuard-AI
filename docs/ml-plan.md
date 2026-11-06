# AirGuard AI — ML Plan

## Three Independent ML Systems

### Model A: Molecular Odor Prediction (OpenPOM)

**Status:** Optional, isolated environment
**Input:** SMILES strings (molecular structure notation)
**Output:** 138 binary odor descriptor probabilities
**Framework:** OpenPOM (MIT) + DeepChem + PyTorch + DGL + RDKit
**Data:** Curated GS-LF merged datasets (user-imported, not bundled)

**Pipeline:**
1. User imports CSV with SMILES + odor descriptor columns
2. Validate SMILES with RDKit
3. Featurize molecules (Morgan fingerprints for RF, GraphConv for MPNN)
4. Train baseline: Random Forest on Morgan FPs (scikit-learn)
5. Train advanced: OpenPOM MPNN (if dependencies available)
6. Evaluate: scaffold-split, per-descriptor AUROC
7. Register model version with metrics

**Limitations:**
- Predicts odor descriptors, NOT chemical hazards
- Requires isolated Python environment
- Dataset licensing restricts commercial redistribution
- High AUROC does not validate hazard detection

### Model B: Environmental Anomaly Detection

**Status:** Core feature, always available with sufficient baseline data
**Input:** Sensor timeseries (PM2.5, VOC, temp, humidity, etc.)
**Output:** Anomaly score (0.0-1.0)
**Framework:** scikit-learn (Isolation Forest, One-Class SVM)

**Pipeline:**
1. Collect baseline readings per room (minimum 48 hours)
2. Extract statistical features per time window
3. Train Isolation Forest on baseline
4. Score new readings against baseline
5. Flag anomalies above configurable threshold

**Levels:**
- L1: Rule-based thresholds (always on, no training needed)
- L2: Isolation Forest anomaly (needs baseline collection)

### Model C: Sensor-Pattern Classifier

**Status:** Requires user-labeled data, starts as "not trained"
**Input:** Labeled sensor recording sessions
**Output:** Event class + confidence + unknown rejection
**Framework:** scikit-learn (Random Forest, Gradient Boosting)

**Safe training classes:**
- baseline_indoor
- cooking
- coffee
- food_aroma
- cleaning
- mixed_unknown

**Pipeline:**
1. User records labeled sessions via Data Collection UI
2. Extract features per session window
3. Split by session ID (grouped validation)
4. Train classifier
5. Add OOD rejection threshold
6. Evaluate: per-class precision/recall, confusion matrix
7. Calibrate probabilities
8. Register model with metadata

## Model Registry

Each model version tracks:
- Model ID, version, type
- Training date
- Dataset identifiers + hash
- Preprocessing config
- Training metrics (per-class)
- Validation metrics (per-class)
- Known limitations
- Approval status (draft → approved → deployed → retired)
- Deployment history

