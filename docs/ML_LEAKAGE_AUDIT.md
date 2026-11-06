# AirGuard AI — Environmental Machine Learning Leakage Audit

**Audit Date:** November 2026  
**Audited Artifacts:** `data/enose/resistance_values.csv`, `services/ml_environment/enose_benchmark.py`, `services/ml_environment/leakage_and_holdout_audit.py`  
**Dataset Provenance:** Marco Rossoni / `TransformerOdorClassification` (GitHub, MIT License)  
**Author:** AirGuard AI ML Systems & Quality Engineering

---

## 1. Executive Summary

This audit investigates the scientific rigor and data leakage risks in machine learning models trained on metal-oxide semiconductor (MOS) gas sensor arrays (specifically the **Bosch BME688**). 

The audit reveals that **reported accuracies exceeding 90% in public literature and early benchmarks are heavily influenced by temporal autocorrelation within single continuous recording runs**. When evaluated under strict forward-time chronological holdouts, test accuracy drops from **90.56% to 51.62%**, driven by physical sensor baseline resistance drift.

> **CRITICAL SCIENTIFIC PRINCIPLE:**  
> Contiguous block grouping (e.g., 40-cycle blocks) mitigates immediate adjacent-sample correlation, but **DOES NOT** constitute an independent session holdout when all samples originate from a single continuous recording session. True cross-session generalization requires multi-day or multi-device recording protocols.

---

## 2. Dataset Structure & Physical Provenance Inspection

### 2.1 File Inspection: `resistance_values.csv`
- **Total Rows:** 35,830 rows = 3,583 ten-step heating cycle sequences.
- **Columns:** `Resistance Gassensor,label`
- **Missing Metadata:** The dataset contains **no timestamps, no device IDs, no ambient temperature/humidity channels, and no session identifiers**.

### 2.2 Sequence Organization & Label Transitions
Analysis of label transitions along the dataset rows reveals a critical finding:
```python
Indices where label changes: [ 8799, 18899, 28639 ]
Row 0     to 8799  (Cycles    0 to  879): Class 0 (Ambient Air,   880 cycles)
Row 8800  to 18899 (Cycles  880 to 1889): Class 1 (Borbone Coffee, 1010 cycles)
Row 18900 to 28639 (Cycles 1890 to 2863): Class 2 (Lavazza Coffee,  974 cycles)
Row 28640 to 35829 (Cycles 2864 to 3582): Class 3 (Primia Coffee,   719 cycles)
```
**Conclusion:** The dataset consists of **four single continuous recording runs**—one monolithic run per odor class.

---

## 3. Systematic Leakage Audit: 5 Risk Categories

### 3.1 Risk 1: Temporal Autocorrelation in Random Splits (CRITICAL)
- **Upstream Implementation:** The original upstream repository (`TransformerOdorClassification/main.py`) applied `train_test_split(..., test_size=0.2, random_state=42, stratify=y)`.
- **Mechanism of Leakage:** Because cycles were sampled randomly from a continuous timeseries, cycle $t$ was placed in the training set and cycle $t+1$ (recorded seconds later) in the test set.
- **Impact:** MOS sensors exhibit thermal hysteresis and slow surface reaction decay. Adjacent cycles have near-identical baseline resistances, allowing models to achieve **91.63% to 97.21%** accuracy merely by memorizing the daily baseline resistance rather than invariant odor features.

### 3.2 Risk 2: Pseudo-Session Grouping (MODERATE)
- **Phase 3 Historical Benchmark:** Grouped sequences into synthetic 40-cycle blocks (`i // 40`) and used `GroupKFold(n_splits=5)`.
- **Audit Finding:** While this prevented cycle $t$ and $t+1$ from being separated across train and test, all 40-cycle blocks of Class $C$ still originated from the **same single continuous chamber exposure**. The sensor remained in the exact same physical chamber state, ambient background, and warm-up epoch.
- **Impact:** Accuracy was **90.56%**, which, while lower than random splitting, still benefited from intra-session constancy.

### 3.3 Risk 3: Overlapping Sensor Windows (CLEAN)
- **Audit Finding:** Sequences of 10 steps were partitioned with step size = 10 (`range(0, len, 10)`). There are **zero overlapping sensor readings** between consecutive sequences.

### 3.4 Risk 4: Preprocessing Fitted on Test Sets (CLEAN)
- **Audit Finding:** Feature transformations in AirGuard AI (`np.log10(R)` and $R_k / R_0$) are computed strictly per-sequence without fitting global scalar scalers across the full dataset. No statistical parameters from the test set leaked into the feature pipeline.

### 3.5 Risk 5: Hyperparameter Tuning on Test Data (CLEAN)
- **Audit Finding:** Model hyperparameters (100 trees, `max_depth=12`, `class_weight='balanced'`) were established a priori without grid-searching over test set accuracy.

---

## 4. Empirical Split Comparison & Drift Quantification

We executed a controlled benchmark (`services/ml_environment/leakage_and_holdout_audit.py`) comparing three split strategies on identical data:

| Evaluation Strategy | Test Accuracy (95% CI) | Macro F1 (95% CI) | Expected Calibration Error (ECE) | Real-World Generalization Meaning |
|---|:---:|:---:|:---:|---|
| **1. Upstream Random Stratified** | **91.63%** [89.68%, 93.72%] | **0.9133** [0.8928, 0.9338] | **0.1050** | **Severely Optimistic**: Exploits adjacent-cycle memorization across splits. |
| **2. Contiguous 40-Cycle Block** | **90.56%** [88.33%, 92.50%] | **0.8908** [0.8651, 0.9122] | **0.1005** | **Historical Benchmark**: Eliminates cycle-to-cycle overlap but shares session. |
| **3. Strict Chronological Holdout** | **51.62%** [48.49%, 55.07%] | **0.3786** [0.3648, 0.3918] | **0.3022** | **True Real-World Simulation**: Train on first 75% of timeline, test on final 25%. |

*All 95% confidence intervals derived from 1,000 empirical bootstrap iterations.*

### Confusion Matrix Under Strict Chronological Holdout:
```
                    PREDICTED
Actual Class      Ambient Air  Borbone  Lavazza  Primia
Ambient Air (0)       217         0        3        0
Borbone Coffee (1)      1       242       10        0
Lavazza Coffee (2)    238         2        4        0
Primia Coffee (3)     174         0        6        0
```

### Analysis of the 51.62% Accuracy Drop:
1. **Borbone Coffee (Class 1)** remained highly recognizable: **95.65% recall** and **99.18% precision**, because its volatile profile produced a large differential swing exceeding baseline drift.
2. **Lavazza (Class 2) & Primia (Class 3)** collapsed into Ambient Air: **238 of 244 Lavazza cycles (97.5%)** and **174 of 180 Primia cycles (96.7%)** were misclassified as Ambient Air.
3. **Physical Explanation:** Over multiple hours of continuous heating (100°C–400°C cycles), the sensor's baseline resistance increased. Later coffee exposures at higher baseline resistance overlapped with earlier ambient air measurements in feature space.

---

## 5. Corrective Engineering Architecture

To achieve genuine reliability in real-world deployment, AirGuard AI implements three architectural guardrails:

1. **Dynamic Baseline Tracking ($R / R_0$):**
   Normalizing each 10-step sequence relative to its Step 0 baseline ($R_k / R_0$) rather than relying solely on raw absolute resistance.
2. **Periodic Fresh-Air Auto-Zeroing:**
   Requiring scheduled fresh-air calibration cycles to re-anchor $R_0$ before executing odor classification.
3. **Unsupervised Anomaly Coupling:**
   Whenever sensor drift causes classification confidence to fall below threshold ($\tau < 0.60$), AirGuard AI routes the observation to **unsupervised anomaly detection** rather than outputting false class predictions.
