import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    brier_score_loss
)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "enose"
)
CSV_4CLASS = os.path.join(DATA_DIR, "resistance_values.csv")
CSV_7CLASS = os.path.join(DATA_DIR, "resistance_values_7classes.csv")
AUDIT_METRICS_PATH = os.path.join(
    os.path.dirname(__file__), "models", "leakage_and_holdout_audit_metrics.json"
)

CLASS_NAMES_4 = ["Ambient Air", "Borbone Coffee", "Lavazza Coffee", "Primia Coffee"]
CLASS_NAMES_7 = CLASS_NAMES_4 + ["Almond Cream", "Thyme Cream", "Marigold Cream"]

def compute_ece(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE) across n_bins probability bins."""
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == y_true)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    return float(ece)

def bootstrap_confidence_intervals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstraps: int = 1000,
    seed: int = 42
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Calculates 95% empirical bootstrap confidence intervals for Accuracy and Macro F1."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    accs = []
    f1s = []
    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, n)
        accs.append(accuracy_score(y_true[idx], y_pred[idx]))
        _, _, f1, _ = precision_recall_fscore_support(
            y_true[idx], y_pred[idx], average="macro", zero_division=0
        )
        f1s.append(f1)
    acc_ci = (float(np.percentile(accs, 2.5)), float(np.percentile(accs, 97.5)))
    f1_ci = (float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5)))
    return acc_ci, f1_ci

def run_comprehensive_leakage_audit():
    print("=================================================================")
    print("AIRGUARD AI — SENSOR ML LEAKAGE & SPLIT METHODOLOGY AUDIT")
    print("=================================================================")

    df = pd.read_csv(CSV_4CLASS)
    res_vals = df.iloc[:, 0].values.astype(float)
    raw_labels = df.iloc[:, 1].values.astype(int)

    seq_len = 10
    num_seqs = len(res_vals) // seq_len

    features_raw = []
    features_drift_robust = []
    labels = []

    for i in range(num_seqs):
        start = i * seq_len
        end = start + seq_len
        w = res_vals[start:end]
        lbl = raw_labels[end - 1]

        # Standard features: log10 and ratio to step 0
        log_res = np.log10(w)
        ratio_to_step0 = w / (w[0] + 1e-6)
        combined_std = np.concatenate([log_res, ratio_to_step0])
        features_raw.append(combined_std)

        # Drift-robust normalized features: dynamic range scaling + derivative profile
        w_min = np.min(w)
        w_max = np.max(w)
        norm_range = (w - w_min) / ((w_max - w_min) + 1e-6)
        diff_profile = np.diff(log_res, prepend=log_res[0])
        combined_robust = np.concatenate([norm_range, diff_profile])
        features_drift_robust.append(combined_robust)

        labels.append(lbl)

    X_raw = np.array(features_raw, dtype=np.float32)
    X_robust = np.array(features_drift_robust, dtype=np.float32)
    y = np.array(labels, dtype=int)

    print(f"Total 10-step sequences: {len(y)}")
    for c_idx, c_name in enumerate(CLASS_NAMES_4):
        print(f"  Class {c_idx} ({c_name}): {np.sum(y == c_idx)} cycles")

    results_audit = {}

    # -------------------------------------------------------------
    # 1. Upstream Random Stratified Split (High Leakage)
    # -------------------------------------------------------------
    print("\n[Audit Split 1] Upstream Random Stratified Split (80/20)")
    X_tr_rnd, X_te_rnd, y_tr_rnd, y_te_rnd = train_test_split(
        X_raw, y, test_size=0.20, random_state=42, stratify=y
    )
    rf_rnd = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_rnd.fit(X_tr_rnd, y_tr_rnd)
    rnd_preds = rf_rnd.predict(X_te_rnd)
    rnd_probs = rf_rnd.predict_proba(X_te_rnd)
    rnd_acc = float(accuracy_score(y_te_rnd, rnd_preds))
    _, _, rnd_f1, _ = precision_recall_fscore_support(y_te_rnd, rnd_preds, average="macro")
    rnd_acc_ci, rnd_f1_ci = bootstrap_confidence_intervals(y_te_rnd, rnd_preds)
    rnd_ece = compute_ece(rnd_probs, y_te_rnd)

    print(f"  Accuracy: {rnd_acc*100:.2f}% (95% CI: [{rnd_acc_ci[0]*100:.2f}%, {rnd_acc_ci[1]*100:.2f}%])")
    print(f"  Macro F1: {rnd_f1:.4f} (95% CI: [{rnd_f1_ci[0]:.4f}, {rnd_f1_ci[1]:.4f}])")
    print(f"  Expected Calibration Error (ECE): {rnd_ece:.4f}")
    print(f"  Scientific Verdict: Severely optimistic. Adjacent cycles in the same run appear across train/test folds.")

    results_audit["upstream_random_stratified"] = {
        "accuracy": round(rnd_acc, 4),
        "accuracy_95ci": [round(x, 4) for x in rnd_acc_ci],
        "macro_f1": round(float(rnd_f1), 4),
        "macro_f1_95ci": [round(x, 4) for x in rnd_f1_ci],
        "ece": round(rnd_ece, 4),
        "leakage_level": "CRITICAL (Adjacent-cycle temporal leakage)"
    }

    # -------------------------------------------------------------
    # 2. Block GroupKFold Split (Phase 3 Benchmark)
    # -------------------------------------------------------------
    print("\n[Audit Split 2] Contiguous 40-Cycle Block Split (Phase 3 Benchmark)")
    block_ids = np.array([i // 40 for i in range(num_seqs)])
    gkf = GroupKFold(n_splits=5)
    tr_blk_idx, te_blk_idx = next(gkf.split(X_raw, y, block_ids))
    rf_blk = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_blk.fit(X_raw[tr_blk_idx], y[tr_blk_idx])
    blk_preds = rf_blk.predict(X_raw[te_blk_idx])
    blk_probs = rf_blk.predict_proba(X_raw[te_blk_idx])
    blk_acc = float(accuracy_score(y[te_blk_idx], blk_preds))
    _, _, blk_f1, _ = precision_recall_fscore_support(y[te_blk_idx], blk_preds, average="macro")
    blk_acc_ci, blk_f1_ci = bootstrap_confidence_intervals(y[te_blk_idx], blk_preds)
    blk_ece = compute_ece(blk_probs, y[te_blk_idx])

    print(f"  Accuracy: {blk_acc*100:.2f}% (95% CI: [{blk_acc_ci[0]*100:.2f}%, {blk_acc_ci[1]*100:.2f}%])")
    print(f"  Macro F1: {blk_f1:.4f} (95% CI: [{blk_f1_ci[0]:.4f}, {blk_f1_ci[1]:.4f}])")
    print(f"  Expected Calibration Error (ECE): {blk_ece:.4f}")
    print(f"  Scientific Verdict: Mitigates immediate neighbor leakage, but blocks originate from the same experimental run.")

    results_audit["phase3_block_groupkfold"] = {
        "accuracy": round(blk_acc, 4),
        "accuracy_95ci": [round(x, 4) for x in blk_acc_ci],
        "macro_f1": round(float(blk_f1), 4),
        "macro_f1_95ci": [round(x, 4) for x in blk_f1_ci],
        "ece": round(blk_ece, 4),
        "leakage_level": "MODERATE (Contiguous block holdout from single continuous session)"
    }

    # -------------------------------------------------------------
    # 3. Strict Chronological Temporal Holdout (First 75% Train, Last 25% Test)
    # -------------------------------------------------------------
    print("\n[Audit Split 3] Strict Chronological Temporal Holdout (75% Past -> 25% Future)")
    tr_chrono_idx = []
    te_chrono_idx = []
    for c in np.unique(y):
        c_idx = np.where(y == c)[0]
        split_pt = int(len(c_idx) * 0.75)
        tr_chrono_idx.extend(c_idx[:split_pt])
        te_chrono_idx.extend(c_idx[split_pt:])

    tr_chrono_idx = np.array(tr_chrono_idx)
    te_chrono_idx = np.array(te_chrono_idx)

    rf_chrono = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_chrono.fit(X_raw[tr_chrono_idx], y[tr_chrono_idx])
    chrono_preds = rf_chrono.predict(X_raw[te_chrono_idx])
    chrono_probs = rf_chrono.predict_proba(X_raw[te_chrono_idx])
    chrono_acc = float(accuracy_score(y[te_chrono_idx], chrono_preds))
    _, _, chrono_f1, _ = precision_recall_fscore_support(y[te_chrono_idx], chrono_preds, average="macro")
    chrono_acc_ci, chrono_f1_ci = bootstrap_confidence_intervals(y[te_chrono_idx], chrono_preds)
    chrono_ece = compute_ece(chrono_probs, y[te_chrono_idx])
    chrono_cm = confusion_matrix(y[te_chrono_idx], chrono_preds)

    print(f"  Accuracy: {chrono_acc*100:.2f}% (95% CI: [{chrono_acc_ci[0]*100:.2f}%, {chrono_acc_ci[1]*100:.2f}%])")
    print(f"  Macro F1: {chrono_f1:.4f} (95% CI: [{chrono_f1_ci[0]:.4f}, {chrono_f1_ci[1]:.4f}])")
    print(f"  Expected Calibration Error (ECE): {chrono_ece:.4f}")
    print("  Confusion Matrix:\n", chrono_cm)

    # Per-class breakdown under temporal holdout
    p_c, r_c, f_c, s_c = precision_recall_fscore_support(y[te_chrono_idx], chrono_preds, average=None)
    chrono_per_class = {}
    for c_idx, c_name in enumerate(CLASS_NAMES_4):
        fp = int(chrono_cm[:, c_idx].sum() - chrono_cm[c_idx, c_idx])
        tn = int(chrono_cm.sum() - chrono_cm[c_idx, :].sum() - chrono_cm[:, c_idx].sum() + chrono_cm[c_idx, c_idx])
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        chrono_per_class[c_name] = {
            "precision": round(float(p_c[c_idx]), 4),
            "recall": round(float(r_c[c_idx]), 4),
            "f1_score": round(float(f_c[c_idx]), 4),
            "support": int(s_c[c_idx]),
            "false_positive_rate": round(fpr, 4)
        }
        print(f"    {c_name:16s} | P: {p_c[c_idx]:.4f} | R: {r_c[c_idx]:.4f} | F1: {f_c[c_idx]:.4f} | FPR: {fpr:.4f}")

    results_audit["chronological_temporal_holdout"] = {
        "accuracy": round(chrono_acc, 4),
        "accuracy_95ci": [round(x, 4) for x in chrono_acc_ci],
        "macro_f1": round(float(chrono_f1), 4),
        "macro_f1_95ci": [round(x, 4) for x in chrono_f1_ci],
        "ece": round(chrono_ece, 4),
        "confusion_matrix": chrono_cm.tolist(),
        "per_class_metrics": chrono_per_class,
        "leakage_level": "ZERO LEAKAGE (Strict forward-time holdout)"
    }

    # -------------------------------------------------------------
    # 4. Drift-Compensated Features on Chronological Holdout
    # -------------------------------------------------------------
    print("\n[Audit Split 4] Drift-Compensated Features on Chronological Holdout")
    rf_robust = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_robust.fit(X_robust[tr_chrono_idx], y[tr_chrono_idx])
    robust_preds = rf_robust.predict(X_robust[te_chrono_idx])
    robust_probs = rf_robust.predict_proba(X_robust[te_chrono_idx])
    robust_acc = float(accuracy_score(y[te_chrono_idx], robust_preds))
    _, _, robust_f1, _ = precision_recall_fscore_support(y[te_chrono_idx], robust_preds, average="macro")
    robust_acc_ci, robust_f1_ci = bootstrap_confidence_intervals(y[te_chrono_idx], robust_preds)
    robust_ece = compute_ece(robust_probs, y[te_chrono_idx])

    print(f"  Accuracy: {robust_acc*100:.2f}% (95% CI: [{robust_acc_ci[0]*100:.2f}%, {robust_acc_ci[1]*100:.2f}%])")
    print(f"  Macro F1: {robust_f1:.4f} (95% CI: [{robust_f1_ci[0]:.4f}, {robust_f1_ci[1]:.4f}])")
    print(f"  Expected Calibration Error (ECE): {robust_ece:.4f}")

    results_audit["drift_compensated_temporal_holdout"] = {
        "accuracy": round(robust_acc, 4),
        "accuracy_95ci": [round(x, 4) for x in robust_acc_ci],
        "macro_f1": round(float(robust_f1), 4),
        "macro_f1_95ci": [round(x, 4) for x in robust_f1_ci],
        "ece": round(robust_ece, 4)
    }

    # -------------------------------------------------------------
    # 5. Out-of-Distribution (OOD) Rejection Comparison
    # -------------------------------------------------------------
    print("\n[Audit Evaluation 5] Out-of-Distribution Rejection on Unseen Aroma-7 Classes")
    df7 = pd.read_csv(CSV_7CLASS)
    res7 = df7.iloc[:, 0].values.astype(float)
    lbl7 = df7.iloc[:, 1].values.astype(int)
    seqs7 = len(res7) // seq_len

    X7_unseen_list = []
    for i in range(seqs7):
        lbl = lbl7[(i + 1) * seq_len - 1]
        if lbl in [4, 5, 6]:
            w = res7[i * seq_len : (i + 1) * seq_len]
            X7_unseen_list.append(np.concatenate([np.log10(w), w / (w[0] + 1e-6)]))
    X7_unseen = np.array(X7_unseen_list, dtype=np.float32)

    ood_probs_blk = rf_blk.predict_proba(X7_unseen)
    ood_probs_chrono = rf_chrono.predict_proba(X7_unseen)

    ood_rejection_audit = {}
    print(f"Total unseen cream sequences evaluated: {len(X7_unseen)}")
    for th in [0.50, 0.60, 0.70, 0.80]:
        rej_blk = float(np.mean(np.max(ood_probs_blk, axis=1) < th))
        rej_chrono = float(np.mean(np.max(ood_probs_chrono, axis=1) < th))
        ood_rejection_audit[f"threshold_{th}"] = {
            "block_model_rejection_rate": round(rej_blk, 4),
            "temporal_model_rejection_rate": round(rej_chrono, 4)
        }
        print(f"  Threshold {th:.2f} -> Block Model Rejection: {rej_blk*100:.1f}%, Chronological Model: {rej_chrono*100:.1f}%")

    results_audit["ood_rejection_audit"] = ood_rejection_audit

    # Save to JSON
    with open(AUDIT_METRICS_PATH, "w") as f:
        json.dump(results_audit, f, indent=2)
    print(f"\nSaved comprehensive audit metrics to: {AUDIT_METRICS_PATH}")

if __name__ == "__main__":
    run_comprehensive_leakage_audit()

