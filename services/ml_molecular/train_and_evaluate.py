import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "molecular", "curated_GS_LF_merged_4983.csv"
)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
CHECKPOINT_PATH = os.path.join(MODEL_DIR, "pom_rf_checkpoint.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "pom_evaluation_metrics.json")

def generate_scaffold(smiles: str) -> str:
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
        return scaffold
    except Exception:
        return ""

def featurize_smiles_list(smiles_list: List[str], fp_size: int = 1024) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=fp_size)
    features = []
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            features.append(np.zeros(fp_size, dtype=np.int8))
        else:
            fp = generator.GetFingerprint(mol)
            arr = np.zeros(fp_size, dtype=np.int8)
            Chem.DataStructs.ConvertToNumpyArray(fp, arr)
            features.append(arr)
    return np.array(features, dtype=np.int8)

def scaffold_split(df: pd.DataFrame, test_ratio: float = 0.20, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset using Bemis-Murcko scaffolds to prevent structural data leakage between train and test sets.
    """
    np.random.seed(seed)
    scaffolds: Dict[str, List[int]] = {}
    for idx, smiles in enumerate(df["nonStereoSMILES"]):
        scaf = generate_scaffold(smiles)
        if scaf not in scaffolds:
            scaffolds[scaf] = []
        scaffolds[scaf].append(idx)

    # Sort scaffold groups from largest to smallest for balanced distribution
    scaffold_groups = sorted(scaffolds.values(), key=len, reverse=True)
    
    train_indices = []
    test_indices = []
    target_test_count = int(len(df) * test_ratio)

    for group in scaffold_groups:
        if len(test_indices) + len(group) <= target_test_count or len(test_indices) == 0:
            test_indices.extend(group)
        else:
            train_indices.extend(group)

    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    return train_df, test_df

def run_benchmark():
    print(f"Loading curated molecular dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} molecules.")

    # Select top descriptors with sufficient positive support (> 100 positive instances)
    all_task_cols = [c for c in df.columns if c not in ["nonStereoSMILES", "descriptors"]]
    task_counts = df[all_task_cols].sum()
    selected_tasks = list(task_counts[task_counts >= 100].index)
    print(f"Selected {len(selected_tasks)} descriptors with >= 100 positive instances.")

    # Scaffold-based split
    train_df, test_df = scaffold_split(df, test_ratio=0.20, seed=42)
    print(f"Scaffold Split: Train = {len(train_df)} molecules, Test = {len(test_df)} molecules.")

    # Featurize
    print("Featurizing molecules using Morgan fingerprints (radius=2, 1024 bits)...")
    X_train = featurize_smiles_list(train_df["nonStereoSMILES"].tolist(), fp_size=1024)
    Y_train = train_df[selected_tasks].values.astype(int)

    X_test = featurize_smiles_list(test_df["nonStereoSMILES"].tolist(), fp_size=1024)
    Y_test = test_df[selected_tasks].values.astype(int)

    # Train multi-output Random Forest
    print("Training Multi-Output Random Forest (100 estimators, max_depth=20)...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, Y_train)

    print("Evaluating model on scaffold-held-out test set...")
    # Predict probabilities on test set
    test_probs_raw = rf.predict_proba(X_test)
    Y_pred_probs = np.zeros_like(Y_test, dtype=float)

    for i in range(len(selected_tasks)):
        classes = rf.classes_[i]
        probs_i = test_probs_raw[i]
        if len(classes) == 1:
            if classes[0] == 1:
                Y_pred_probs[:, i] = 1.0
            else:
                Y_pred_probs[:, i] = 0.0
        else:
            # Column 1 corresponds to class 1 (presence of descriptor)
            Y_pred_probs[:, i] = probs_i[:, 1]

    # Threshold for binary predictions (default 0.35 given class imbalance)
    threshold = 0.35
    Y_pred_bin = (Y_pred_probs >= threshold).astype(int)

    # Calculate metrics
    per_descriptor_metrics = {}
    valid_auc_scores = []
    valid_f1_scores = []

    for idx, desc in enumerate(selected_tasks):
        y_true = Y_test[:, idx]
        y_pred = Y_pred_bin[:, idx]
        y_prob = Y_pred_probs[:, idx]

        support_pos = int(np.sum(y_true))
        support_neg = int(len(y_true) - support_pos)

        # ROC-AUC requires both positive and negative samples in test set
        if support_pos > 0 and support_neg > 0:
            auc = float(roc_auc_score(y_true, y_prob))
            valid_auc_scores.append(auc)
        else:
            auc = None

        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        valid_f1_scores.append(f1)

        per_descriptor_metrics[desc] = {
            "roc_auc": round(auc, 4) if auc is not None else "N/A",
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "test_support_positive": support_pos,
            "test_support_negative": support_neg
        }

    macro_auc = float(np.mean(valid_auc_scores)) if valid_auc_scores else 0.0
    macro_f1 = float(np.mean(valid_f1_scores)) if valid_f1_scores else 0.0

    print(f"Benchmark Results:")
    print(f"  Macro ROC-AUC: {macro_auc:.4f} across {len(valid_auc_scores)} descriptors")
    print(f"  Macro F1 Score (threshold={threshold}): {macro_f1:.4f}")

    # Top performing descriptors
    sorted_by_auc = sorted(
        [(k, v["roc_auc"]) for k, v in per_descriptor_metrics.items() if v["roc_auc"] != "N/A"],
        key=lambda x: x[1],
        reverse=True
    )
    print("Top 10 Descriptors by Test ROC-AUC:")
    for desc, score in sorted_by_auc[:10]:
        print(f"  {desc:15s}: ROC-AUC = {score:.4f}, F1 = {per_descriptor_metrics[desc]['f1_score']:.4f}")

    # Save model checkpoint
    checkpoint = {
        "model": rf,
        "descriptors": selected_tasks,
        "n_bits": 1024,
        "threshold": threshold,
        "training_date": datetime.now().isoformat(),
        "model_type": "Morgan_FP_RandomForest_ScaffoldSplit",
        "dataset_name": "OpenPOM_curated_GS_LF_merged_4983",
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "macro_roc_auc": round(macro_auc, 4),
        "macro_f1": round(macro_f1, 4)
    }
    joblib.dump(checkpoint, CHECKPOINT_PATH)
    print(f"Saved trained model checkpoint to {CHECKPOINT_PATH}")

    # Save detailed evaluation metrics
    evaluation_summary = {
        "model_architecture": "Random Forest on Morgan Fingerprints (radius=2, 1024-bits)",
        "model_type_label": "Morgan-FP Random Forest Baseline",
        "dataset": "curated_GS_LF_merged_4983 (OpenPOM GoodScents + Leffingwell)",
        "dataset_license": "MIT License (Copyright 2023 Aryan Amit Barsainyan / BioMachineLearning)",
        "total_molecules": len(df),
        "train_molecules": len(train_df),
        "test_molecules": len(test_df),
        "split_method": "Bemis-Murcko Scaffold Split (Zero Structural Leakage)",
        "threshold": threshold,
        "macro_roc_auc": round(macro_auc, 4),
        "macro_f1": round(macro_f1, 4),
        "num_evaluated_descriptors": len(selected_tasks),
        "top_performers": [
            {"descriptor": d, "roc_auc": s, "f1": per_descriptor_metrics[d]["f1_score"]}
            for d, s in sorted_by_auc[:15]
        ],
        "per_descriptor_metrics": per_descriptor_metrics,
        "openpom_comparison": {
            "openpom_architecture": "Message Passing Neural Network (MPNN / Graph Convolution)",
            "openpom_features": "3D/2D Molecular Graph (atoms + bonds featurization via DeepChem)",
            "openpom_tasks": 138,
            "openpom_reported_macro_auc": 0.885,
            "rf_baseline_macro_auc": round(macro_auc, 4),
            "architectural_difference": "OpenPOM utilizes iterative edge/node message passing to capture subtle conformation and spatial stereo-chemistry, whereas the Morgan-FP Random Forest baseline encodes local 2D circular substructure bit-vectors without stereochemical coordinates."
        }
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(evaluation_summary, f, indent=2)
    print(f"Saved evaluation metrics to {METRICS_PATH}")

if __name__ == "__main__":
    run_benchmark()
