# AirGuard AI — Electronic-Nose & Environmental Model Evaluation

**Document Version:** 2.0.0  
**Last Updated:** November 2026  
**Module:** `services/ml_environment`  
**Evaluation Script:** `services/ml_environment/enose_benchmark.py`  
**Dataset Source:** Marco Rossoni / `TransformerOdorClassification` (GitHub)  
**Dataset License:** MIT License (Copyright © 2025 Marco Rossoni)

---

## 1. Executive Summary

This evaluation document details the empirical benchmarking of machine learning algorithms for **electronic-nose (e-nose)** sensor sequence classification within AirGuard AI. Using real sensor recordings from a **Bosch BME688** gas sensor array executing controlled 10-step temperature profiles, we evaluate both tree-based ensemble baselines and a deep sequence transformer (**ConvTran**), quantify false-positive rates on ambient clean air, and assess **Out-of-Distribution (OOD) unknown-class rejection**.

> **SAFETY MANDATE:**  
> Electronic-nose classifications represent statistical pattern recognition over transient metal-oxide semiconductor (MOS) resistance curves. They **DO NOT** constitute chemical spectrometry, quantitative concentration assays, or life-safety toxic/combustible gas detection.

---

## 2. Sensor Technology & Dataset Provenance

### 2.1 Bosch BME688 MOS Sensor Array
The Bosch BME688 is an environmental sensor combining gas, temperature, humidity, and barometric pressure sensing. Its metal-oxide semiconductor (MOS) gas sensor incorporates an internal heating element capable of cycling through discrete temperature steps (typically 100°C to 400°C). Different VOCs undergo catalytic redox reactions at characteristic activation temperatures, creating a multi-dimensional "odor fingerprint" across the temperature cycle.

### 2.2 Datasets & Benchmark Structure
We benchmarked two curated datasets collected under controlled conditions:

| Dataset | File | Total Steps | Sequences (Length 10) | Classes | Class Distribution |
|---|---|---|---|---|---|
| **CoffeePow-4** | `resistance_values.csv` | 35,830 | **3,583** | 4 | Ambient Air (880), Borbone Coffee (1,010), Lavazza Coffee (974), Primia Coffee (719) |
| **Aroma-7** | `resistance_values_7classes.csv` | 47,504 | **4,750** | 7 | CoffeePow-4 classes + Almond Cream (372), Thyme Cream (431), Marigold Cream (364) |

- **License:** MIT License, Copyright © 2025 Marco Rossoni.
- **Physical Verification Status:** Tested against physical sensor recording dumps; models persisted to `services/ml_environment/models/`.

---

## 3. Preprocessing & Leakage-Free Session Grouping

### 3.1 10-Step Sequence Construction
Each 10 consecutive raw resistance readings correspond to one full heating cycle (Step 0 to Step 9). For each sequence $i$, we compute:
1. **Logarithmic Resistances:** $f_{\log}(k) = \log_{10}(R_k)$ for $k \in \{0, \dots, 9\}$.
2. **Normalized Baseline Ratios:** $f_{\text{ratio}}(k) = \frac{R_k}{R_0 + \epsilon}$ for $k \in \{0, \dots, 9\}$.
3. **Combined Feature Vector:** $\mathbf{x}_i \in \mathbb{R}^{20}$.

### 3.2 Session-Grouped Split (Preventing Temporal Leakage)
In continuous gas sensor operation, adjacent cycles share thermal hysteresis and sensor drift. A naive random split would place adjacent cycles in train and test folds, artificially inflating accuracy:
- **Session Grouping:** Cycles are partitioned into contiguous blocks of 40 cycles (representing independent recording runs).
- **Split Protocol:** `GroupKFold(n_splits=5)` partitioning on session blocks.
- **Partition Distribution:**
  - **Train Set:** 2,863 sequences across 72 independent session blocks (80%).
  - **Test Set:** 720 sequences across 18 held-out session blocks (20%).

---

## 4. Benchmark Model Evaluation Results

Three distinct architectures were trained and evaluated on identical test partitions:

| Model Architecture | Test Accuracy | Macro Precision | Macro Recall | Macro F1 | Edge / Production Profile |
|---|---|---|---|---|---|
| **HistGradientBoosting** | **91.67%** | **91.43%** | **90.81%** | **0.9072** | **Recommended for Production**: Ultra-fast (<1 ms inference), minimal RAM footprint |
| **Random Forest Baseline** | **90.56%** | **91.28%** | **88.58%** | **0.8908** | **High Interpretability**: 100 trees, robust to individual step noise |
| **ConvTran (1D-CNN + Transformer)** | **61.11%** | **68.27%** | **58.74%** | **0.5614** | **PyTorch Edge Model**: 24k parameters (115 KB weight file), 2-layer multihead attention |

*Observation: On sequences of length 10, gradient-boosted trees and random forests outperform deep sequence transformers by effectively utilizing the engineered baseline ratio and log-resistance features without overfitting small-sample sequence dependencies.*

---

## 5. Detailed Per-Class Performance & False-Alarm Analysis

The detailed breakdown for the **Random Forest Baseline** ($N_{\text{test}} = 720$ sequences) is documented below:

### 5.1 Confusion Matrix
```
                    PREDICTED
Actual Class      Ambient Air  Borbone  Lavazza  Primia
Ambient Air (0)       192         0        6        2
Borbone Coffee (1)      0       197        3        0
Lavazza Coffee (2)      4         1      175        4
Primia Coffee (3)      10         0       38       88
```

### 5.2 Per-Class Precision, Recall, F1, and False-Positive Rate (FPR)
| Class | Precision | Recall | F1-Score | Support | False Positives | True Negatives | False Positive Rate (FPR) |
|---|---|---|---|---|---|---|---|
| **Ambient Air** | **0.9320** | **0.9600** | **0.9458** | 200 | 14 | 506 | **0.0269 (2.69%)** |
| **Borbone Coffee** | **0.9949** | **0.9850** | **0.9899** | 200 | 1 | 519 | **0.0019 (0.19%)** |
| **Lavazza Coffee** | **0.7883** | **0.9511** | **0.8621** | 184 | 47 | 489 | **0.0877 (8.77%)** |
| **Primia Coffee** | **0.9362** | **0.6471** | **0.7652** | 136 | 6 | 578 | **0.0103 (1.03%)** |

### 5.3 False Alarm Rate on Clean Ambient Air
A critical safety requirement is that ambient clean air must rarely trigger odor alarms:
- **Ambient Air FPR:** $\frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{14}{14 + 506} = \mathbf{2.69\%}$.
- Out of 520 non-ambient coffee sequences, only 14 were erroneously classified as ambient air (2.69% false-negative odor rate), while 96.0% of true clean air cycles were correctly identified.

---

## 6. Out-of-Distribution (OOD) Unknown-Class Rejection

Real-world deployment inevitably encounters odors outside the training domain. To assess open-world reliability, we evaluated the CoffeePow-4 trained classifier on **1,167 unseen test sequences** from Aroma-7 (Almond Cream, Thyme Cream, Marigold Cream):

| Confidence Threshold ($\tau$) | Flagged as `unknown_pattern` | Unknown Rejection Rate | Erroneously Classified as Known |
|---|---|---|---|
| **$\tau = 0.50$** | 0 / 1,167 | **0.0%** | 100.0% |
| **$\tau = 0.60$** | 90 / 1,167 | **7.7%** | 92.3% |
| **$\tau = 0.70$** | 90 / 1,167 | **7.7%** | 92.3% |
| **$\tau = 0.80$** | 91 / 1,167 | **7.8%** | 92.2% |

### Key Safety Finding:
Even at a high confidence threshold ($\tau = 0.80$), tree-based classifiers exhibit overconfidence on out-of-distribution MOS resistance curves, rejecting only ~7.8% of unseen cosmetics as unknown.
**Engineering Action Implemented:** AirGuard AI couples classification with **unsupervised anomaly detection (Isolation Forest & Dynamic Baseline Z-Score)**. When an anomaly is detected without a high-confidence class match, the system categorizes the event as `unidentified_environmental_anomaly` rather than fabricating an odor class.

---

## 7. Model Checkpoint Registry & Integrity

The following verified model checkpoints are committed in `services/ml_environment/models/`:
- `enose_rf_checkpoint.joblib` (Random Forest, 100 estimators, 10-step features)
- `enose_convtran_checkpoint.pt` (PyTorch ConvTran sequence transformer state dict)
- `enose_evaluation_metrics.json` (Full JSON benchmark evaluation metrics)

The metrics are served live via the API endpoint `GET /api/v1/models/enose/benchmark` and rendered in the **AI Model Lab UI**.

