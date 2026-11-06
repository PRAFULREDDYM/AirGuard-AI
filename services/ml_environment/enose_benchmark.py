import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    accuracy_score
)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "enose"
)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

CSV_4CLASS = os.path.join(DATA_DIR, "resistance_values.csv")
CSV_7CLASS = os.path.join(DATA_DIR, "resistance_values_7classes.csv")
METRICS_PATH = os.path.join(MODEL_DIR, "enose_evaluation_metrics.json")
RF_CHECKPOINT_PATH = os.path.join(MODEL_DIR, "enose_rf_checkpoint.joblib")
NN_CHECKPOINT_PATH = os.path.join(MODEL_DIR, "enose_convtran_checkpoint.pt")

CLASS_NAMES_4 = [
    "Ambient Air",
    "Borbone Coffee",
    "Lavazza Coffee",
    "Primia Coffee"
]

CLASS_NAMES_7 = [
    "Ambient Air",
    "Borbone Coffee",
    "Lavazza Coffee",
    "Primia Coffee",
    "Almond Cream",
    "Thyme Cream",
    "Marigold Cream"
]

# -------------------------------------------------------------
# ConvTran / 1D-CNN Transformer Edge Model Architecture
# -------------------------------------------------------------
class ConvTran1D(nn.Module):
    def __init__(self, seq_len: int = 10, num_classes: int = 4, d_model: int = 32, nhead: int = 4, num_layers: int = 2):
        super(ConvTran1D, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=d_model, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(d_model)
        self.relu = nn.ReLU()
        
        self.pos_embedding = nn.Parameter(torch.randn(1, seq_len, d_model) * 0.02)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=64,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        # x: (batch_size, 10) -> (batch_size, 1, 10)
        x = x.unsqueeze(1)
        x = self.relu(self.bn1(self.conv1(x)))
        # x: (batch_size, d_model, 10) -> (batch_size, 10, d_model)
        x = x.permute(0, 2, 1) + self.pos_embedding
        x = self.transformer(x)
        # Global average pooling across time steps
        x = x.mean(dim=1)
        logits = self.classifier(x)
        return logits


# -------------------------------------------------------------
# Data Preprocessing & Session-Grouped Splitting
# -------------------------------------------------------------
def load_and_preprocess_enose(csv_path: str, seq_len: int = 10, session_block_size: int = 40):
    """
    Loads raw BME688 resistance timeseries, chunks into 10-step heating cycle sequences,
    computes log10 resistance features, and assigns continuous block session IDs
    to prevent temporal data leakage during cross-validation.
    """
    df = pd.read_csv(csv_path)
    res_vals = df.iloc[:, 0].values.astype(float)
    raw_labels = df.iloc[:, 1].values.astype(int)

    # Sanity checks
    assert not np.isnan(res_vals).any(), "Dataset contains NaN resistance values"
    assert (res_vals > 0).all(), "Dataset contains non-positive resistance values"

    num_seqs = len(res_vals) // seq_len
    features = []
    labels = []
    session_ids = []

    for i in range(num_seqs):
        start = i * seq_len
        end = start + seq_len
        window = res_vals[start:end]
        lbl = raw_labels[end - 1]
        
        # Features: log10 resistances and normalized ratio relative to step 0
        log_res = np.log10(window)
        ratio_to_step0 = window / (window[0] + 1e-6)
        combined_feat = np.concatenate([log_res, ratio_to_step0])

        features.append(combined_feat)
        labels.append(lbl)
        session_ids.append(i // session_block_size)

    return np.array(features, dtype=np.float32), np.array(labels, dtype=int), np.array(session_ids, dtype=int)


def run_enose_benchmarks():
    print("=================================================================")
    print("AIRGUARD AI — ELECTRONIC-NOSE SENSOR BENCHMARK & EVALUATION")
    print("=================================================================")
    print(f"Loading BME688 CoffeePow-4 dataset from: {CSV_4CLASS}")
    X4, y4, sessions4 = load_and_preprocess_enose(CSV_4CLASS, seq_len=10, session_block_size=40)
    print(f"Total sequences: {len(X4)}, Features per sequence: {X4.shape[1]}")
    print(f"Unique recording sessions (blocks of 40 cycles): {len(np.unique(sessions4))}")
    print(f"Class distribution: {dict(pd.Series(y4).value_counts())}")

    # Session-grouped train/test split (80% train, 20% test via GroupKFold)
    gkf = GroupKFold(n_splits=5)
    train_idx, test_idx = next(gkf.split(X4, y4, sessions4))

    X_train, y_train = X4[train_idx], y4[train_idx]
    X_test, y_test = X4[test_idx], y4[test_idx]
    print(f"Session Split: Train = {len(X_train)} seqs ({len(np.unique(sessions4[train_idx]))} sessions), "
          f"Test = {len(X_test)} seqs ({len(np.unique(sessions4[test_idx]))} sessions)")

    # 1. Baseline: Random Forest
    print("\n--- Model 1: Random Forest Baseline ---")
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    rf_prec, rf_rec, rf_f1, _ = precision_recall_fscore_support(y_test, rf_preds, average="macro")
    print(f"RF Test Accuracy: {rf_acc:.4f}, Macro F1: {rf_f1:.4f}")

    # 2. Baseline: HistGradientBoosting
    print("\n--- Model 2: HistGradientBoosting Baseline ---")
    gb = HistGradientBoostingClassifier(max_iter=100, max_depth=8, random_state=42)
    gb.fit(X_train, y_train)
    gb_preds = gb.predict(X_test)
    gb_acc = accuracy_score(y_test, gb_preds)
    gb_prec, gb_rec, gb_f1, _ = precision_recall_fscore_support(y_test, gb_preds, average="macro")
    print(f"GB Test Accuracy: {gb_acc:.4f}, Macro F1: {gb_f1:.4f}")

    # 3. Neural Architecture: ConvTran (1D-CNN + Multihead Self-Attention)
    print("\n--- Model 3: ConvTran 1D-CNN Transformer (PyTorch) ---")
    # For ConvTran, use the 10 raw log10 steps as input sequence
    X4_seq = X4[:, :10]
    X_train_seq = torch.tensor(X4_seq[train_idx], dtype=torch.float32)
    y_train_tensor = torch.tensor(y4[train_idx], dtype=torch.long)
    X_test_seq = torch.tensor(X4_seq[test_idx], dtype=torch.float32)
    y_test_tensor = torch.tensor(y4[test_idx], dtype=torch.long)

    train_loader = DataLoader(TensorDataset(X_train_seq, y_train_tensor), batch_size=32, shuffle=True)
    
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Training ConvTran on device: {device}")
    model = ConvTran1D(seq_len=10, num_classes=4, d_model=32, nhead=4, num_layers=2).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(15):
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            out = model(batch_x)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/15 - Loss: {total_loss / len(train_loader):.4f}")

    model.eval()
    with torch.no_grad():
        test_out = model(X_test_seq.to(device))
        nn_probs = torch.softmax(test_out, dim=1).cpu().numpy()
        nn_preds = np.argmax(nn_probs, axis=1)

    nn_acc = accuracy_score(y_test, nn_preds)
    nn_prec, nn_rec, nn_f1, _ = precision_recall_fscore_support(y_test, nn_preds, average="macro")
    print(f"ConvTran Test Accuracy: {nn_acc:.4f}, Macro F1: {nn_f1:.4f}")

    # 4. Detailed Per-Class Evaluation on Best Model (Random Forest)
    print("\n=================================================================")
    print("DETAILED PER-CLASS EVALUATION (Random Forest Benchmark)")
    print("=================================================================")
    cm = confusion_matrix(y_test, rf_preds)
    print("Confusion Matrix:\n", cm)

    per_class_metrics = {}
    p, r, f, s = precision_recall_fscore_support(y_test, rf_preds, average=None)
    for c_idx, c_name in enumerate(CLASS_NAMES_4):
        # False Positive Rate: FP / (FP + TN)
        fp = int(cm[:, c_idx].sum() - cm[c_idx, c_idx])
        tn = int(cm.sum() - cm[c_idx, :].sum() - cm[:, c_idx].sum() + cm[c_idx, c_idx])
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        per_class_metrics[c_name] = {
            "precision": round(float(p[c_idx]), 4),
            "recall": round(float(r[c_idx]), 4),
            "f1_score": round(float(f[c_idx]), 4),
            "support": int(s[c_idx]),
            "false_positive_rate": round(fpr, 4),
            "false_positives": fp,
            "true_negatives": tn
        }
        print(f"  {c_name:16s} | P: {p[c_idx]:.4f} | R: {r[c_idx]:.4f} | F1: {f[c_idx]:.4f} | FPR: {fpr:.4f}")

    # 5. Unknown-Class Rejection Test (OOD Evaluation)
    print("\n=================================================================")
    print("OUT-OF-DISTRIBUTION (OOD) UNKNOWN-CLASS REJECTION TEST")
    print("=================================================================")
    print(f"Loading Aroma-7 dataset from: {CSV_7CLASS}")
    X7, y7, _ = load_and_preprocess_enose(CSV_7CLASS, seq_len=10)
    
    # Filter for the 3 unseen cream classes (labels 4, 5, 6)
    cream_mask = np.isin(y7, [4, 5, 6])
    X_unseen = X7[cream_mask]
    y_unseen = y7[cream_mask]
    print(f"Total unseen class sequences (Almond, Thyme, Marigold Creams): {len(X_unseen)}")

    ood_probs = rf.predict_proba(X_unseen)
    max_ood_probs = np.max(ood_probs, axis=1)

    thresholds = [0.50, 0.60, 0.70, 0.80]
    ood_rejection_results = {}
    for th in thresholds:
        rejected_count = int(np.sum(max_ood_probs < th))
        rejection_rate = rejected_count / len(max_ood_probs)
        ood_rejection_results[f"threshold_{th}"] = {
            "threshold": th,
            "rejected_as_unknown": rejected_count,
            "total_unseen_samples": len(max_ood_probs),
            "unknown_rejection_rate": round(rejection_rate, 4),
            "false_classification_rate": round(1.0 - rejection_rate, 4)
        }
        print(f"  Confidence Threshold {th:.2f} -> Rejection Rate: {rejection_rate*100:.1f}% "
              f"({rejected_count}/{len(max_ood_probs)} flagged as 'unknown_pattern')")

    # 6. Save Model Checkpoints & Complete Metrics
    checkpoint = {
        "model": rf,
        "classes": CLASS_NAMES_4,
        "features": ["log10_r_step0_to_9", "ratio_r_step0_to_9"],
        "training_date": datetime.now().isoformat(),
        "model_type": "BME688_RandomForest_10Step",
        "dataset_name": "CoffeePow-4 (BME688 10-Step Temperature Cycle)",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": round(rf_acc, 4),
        "macro_f1": round(rf_f1, 4)
    }
    joblib.dump(checkpoint, RF_CHECKPOINT_PATH)
    print(f"\nSaved RF Checkpoint to: {RF_CHECKPOINT_PATH}")

    torch.save(model.state_dict(), NN_CHECKPOINT_PATH)
    print(f"Saved ConvTran Checkpoint to: {NN_CHECKPOINT_PATH}")

    # Comprehensive evaluation document
    results = {
        "dataset": "Bosch BME688 Electronic-Nose (CoffeePow-4 & Aroma-7)",
        "dataset_license": "MIT License (Copyright 2025 Marco Rossoni / mrc-rossoni)",
        "sensor_technology": "Bosch BME688 Metal-Oxide Semiconductor (MOS) Gas Sensor Array",
        "heating_cycle": "10-Step Temperature Profiles (100°C to 400°C)",
        "session_split": "Session-Grouped Blocks (40 cycles/block) via GroupKFold to eliminate temporal data leakage",
        "evaluation_date": datetime.now().isoformat(),
        "models_benchmarked": {
            "RandomForest": {
                "accuracy": round(rf_acc, 4),
                "macro_precision": round(rf_prec, 4),
                "macro_recall": round(rf_rec, 4),
                "macro_f1": round(rf_f1, 4)
            },
            "HistGradientBoosting": {
                "accuracy": round(gb_acc, 4),
                "macro_precision": round(gb_prec, 4),
                "macro_recall": round(gb_rec, 4),
                "macro_f1": round(gb_f1, 4)
            },
            "ConvTran_Transformer": {
                "accuracy": round(nn_acc, 4),
                "macro_precision": round(nn_prec, 4),
                "macro_recall": round(nn_rec, 4),
                "macro_f1": round(nn_f1, 4),
                "architecture": "1D Convolution (k=3) + 2-layer Multi-head Self-Attention (4 heads) + Linear Head"
            }
        },
        "confusion_matrix": cm.tolist(),
        "class_labels": CLASS_NAMES_4,
        "per_class_metrics": per_class_metrics,
        "ambient_air_false_alarm_rate": per_class_metrics["Ambient Air"]["false_positive_rate"],
        "ood_unknown_rejection": ood_rejection_results,
        "safety_and_provenance_disclaimer": "Electronic-nose classifications are statistical pattern recognitions over transient MOS resistance curves. They do NOT constitute quantitative chemical concentration assays and MUST NOT be used for toxic or combustible gas hazard determination."
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Enose Evaluation Metrics to: {METRICS_PATH}")

if __name__ == "__main__":
    run_enose_benchmarks()

