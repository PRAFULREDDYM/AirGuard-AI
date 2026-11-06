# AirGuard AI — Independent Session Evaluation & Calibration Report

**Document Version:** 2.0.0  
**Last Updated:** November 2026  
**Module:** `services/ml_environment`  
**Evaluation Script:** `services/ml_environment/leakage_and_holdout_audit.py`  
**Dataset Artifact:** `data/enose/resistance_values.csv` (CoffeePow-4) & `data/enose/resistance_values_7classes.csv` (Aroma-7)

---

## 1. Scope & Methodological Integrity

This report establishes the verified performance of electronic-nose classifiers under realistic holdout conditions. In environmental sensing, models rarely encounter the exact ambient conditions, temperature plate drift, and humidity levels present during training.

We evaluate performance across three axes:
1. **Splitting Methodology Comparison:** Random Stratified vs. 40-Cycle Block vs. Strict Chronological Holdout.
2. **Statistical Confidence Intervals:** 1,000 bootstrap resamples providing empirical 95% confidence intervals.
3. **Probability Calibration & Out-of-Distribution Rejection:** Expected Calibration Error (ECE) and rejection of unseen cosmetic scents (Aroma-7).

---

## 2. Recomputed Performance Metrics Across Split Methodologies

| Metric | Upstream Random Stratified | Phase 3 Block GroupKFold | Strict Chronological Holdout |
|---|:---:|:---:|:---:|
| **Test Accuracy** | **91.63%** [89.68%, 93.72%] | **90.56%** [88.33%, 92.50%] | **51.62%** [48.49%, 55.07%] |
| **Macro F1 Score** | **0.9133** [0.8928, 0.9338] | **0.8908** [0.8651, 0.9122] | **0.3786** [0.3648, 0.3918] |
| **Expected Calibration Error (ECE)** | **0.1050** | **0.1005** | **0.3022** |
| **Ambient Air False Positive Rate** | **0.0192 (1.92%)** | **0.0269 (2.69%)** | **0.6100 (61.0%)** |
| **Evaluation Bias Level** | Severe optimistic bias | Moderate intra-session bias | Zero temporal leakage |

*Note on Historical Benchmarks: The Phase 3 benchmark of 90.56% accuracy remains documented as the reference for intra-session classification, while 51.62% represents the rigorous forward-time generalization floor without dynamic baseline recalibration.*

---

## 3. Detailed Per-Class Breakdown (Strict Chronological Holdout)

Evaluating on the final 25% of each class timeline ($N_{\text{test}} = 895$ cycles):

| Odor Class | Precision | Recall | F1-Score | Support ($N_{\text{test}}$) | False Positive Rate (FPR) | Primary Error Mode |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Ambient Air** | 0.3444 | **0.9864** | 0.5106 | 220 | 0.6100 | Late-stage coffee cycles falsely predicted as ambient air |
| **Borbone Coffee** | **0.9918** | **0.9565** | **0.9738** | 253 | **0.0031** | Robust; high signal-to-noise ratio above drift floor |
| **Lavazza Coffee** | 0.1739 | 0.0164 | 0.0300 | 244 | 0.0291 | Misclassified as Ambient Air due to baseline upward drift |
| **Primia Coffee** | 0.0000 | 0.0000 | 0.0000 | 178 | 0.0000 | Completely absorbed by Ambient Air class |

---

## 4. Probability Calibration Analysis

### 4.1 Expected Calibration Error (ECE)
A calibrated classifier outputs probabilities that match real empirical frequencies (e.g., when predicting 80% confidence, the model should be correct 80% of the time).
- **Block Split ECE:** **0.1005** (Well-calibrated within the same session).
- **Chronological Holdout ECE:** **0.3022** (Severely miscalibrated; the model outputs 70%–85% confidence while achieving only 51.6% accuracy).

### 4.2 Reliability Curve Insight
Under forward-time drift, the model becomes **overconfident in wrong predictions** because drifted feature vectors land in regions of feature space that had high class density in the training fold.

---

## 5. Out-of-Distribution (OOD) Unknown-Class Rejection

Using the model trained on CoffeePow-4, we evaluated **1,167 unseen test sequences** from the Aroma-7 dataset (Almond Cream, Thyme Cream, Marigold Cream):

| Confidence Threshold ($\tau$) | Block Model Rejection Rate | Chronological Model Rejection Rate | Safety Assessment |
|---|:---:|:---:|---|
| **$\tau = 0.50$** | 0.0% | 7.7% | Unsafe: 100% of unknown scents assigned to known classes |
| **$\tau = 0.60$** | 7.7% | 7.7% | Marginal |
| **$\tau = 0.70$** | 7.7% | 7.8% | Marginal |
| **$\tau = 0.80$** | 7.8% | **11.6%** | Preferred threshold for production rejection |

### Key Architectural Conclusion:
Static thresholding on softmax probabilities is insufficient for robust open-world unknown odor rejection. AirGuard AI enforces **two-layer filtering**:
1. Layer 1: **Dynamic Baseline Z-Score & Isolation Forest** detects novelty in raw sensor resistance curves.
2. Layer 2: **Supervised Classifier with $\tau \ge 0.75$ cutoff**; if confidence is low, the event is permanently tagged `unidentified_environmental_anomaly`.

---

## 6. Hardware Session Data Logging Protocol

To eliminate intra-session bias in physical hardware testing, follow this protocol:
1. **Multi-Day Sampling:** Record calibration sessions on at least 3 distinct calendar days.
2. **Thermal Stabilization:** Record 15 minutes of clean air baseline prior to every exposure.
3. **Session Tagging:** Hardware firmware must transmit a unique `session_uuid` in the MQTT JSON payload (`airguard/telemetry/{device_id}`).
4. **Holdout Evaluation:** Hold out entire `session_uuid` blocks for test splits.
