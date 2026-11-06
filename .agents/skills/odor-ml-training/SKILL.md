---
name: odor-ml-training
description: >-
  Guide for OpenPOM molecular odor prediction, CSV dataset inspection, RDKit/DeepChem/PyTorch
  pipeline, model training, evaluation with molecular-aware splits, and inference.
---

# Odor ML Training Skill

## Purpose
Manage the molecular odor prediction pipeline using OpenPOM and curated GS-LF datasets. This is SEPARATE from environmental sensor ML.

## Key Distinction
- **Molecular odor model:** Takes SMILES strings → predicts odor descriptors
- **Environmental sensor model:** Takes sensor timeseries → detects patterns
- These are DIFFERENT systems. Never mix their inputs/outputs.

## Dataset Inspection Procedure

1. Load CSV files: `curated_GS_LF_merged_4983.csv` and `curated_GS_LF_merged_4984.csv`
2. Check columns: expect SMILES column + binary odor descriptor columns
3. Count records and unique SMILES
4. Validate SMILES with RDKit `Chem.MolFromSmiles()`
5. Check for duplicates between datasets
6. Analyze label distributions (class imbalance)
7. Check for missing values
8. Document differences between dataset versions
9. Verify provenance: Goodscents + Leffingwell merged dataset

## Training Pipeline

1. **Environment setup:** Isolated venv with PyTorch, RDKit, DeepChem, OpenPOM
2. **Data loading:** Parse CSV, validate SMILES, create molecular graphs
3. **Featurization:** Morgan fingerprints for RF baseline; GraphConv/MPNN for neural
4. **Splitting:** Scaffold split or molecular-identity-aware split (NOT random)
5. **Baseline:** Random Forest on Morgan fingerprints (fast, interpretable)
6. **Advanced:** OpenPOM MPNN if dependencies permit
7. **Evaluation:** Per-descriptor AUROC, macro AUROC, PR curves
8. **Versioning:** Save model, config, metrics, dataset hash

## Evaluation Rules

- Use scaffold or Butina cluster splits, NOT random splits
- Report per-descriptor metrics, not just macro average
- Track dataset version alongside model version
- A high AUROC on odor prediction says NOTHING about hazard detection
- Do not evaluate on training set molecules

## Dependency Isolation

OpenPOM requires specific versions of DeepChem, DGL/PyTorch. These may conflict with the main app environment. Use a separate virtual environment or conda env.

Core app MUST work without OpenPOM installed.

## Validation Checklist

- [ ] CSV datasets inspected and documented
- [ ] SMILES validation with RDKit
- [ ] Proper train/test split (scaffold or cluster-based)
- [ ] Baseline model trained and evaluated
- [ ] Metrics include per-descriptor breakdown
- [ ] Model versioned with dataset hash
- [ ] Dependencies isolated from main app
- [ ] License/provenance documented
- [ ] No confusion between molecular and environmental models

