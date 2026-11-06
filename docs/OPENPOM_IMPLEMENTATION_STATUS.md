# AirGuard AI — OpenPOM Implementation & Feasibility Audit

**Document Version:** 2.0.0  
**Last Updated:** November 2026  
**Module:** `services/ml_molecular`  
**Upstream Repository:** `BioMachineLearning/openpom` (GitHub)  
**Upstream License:** MIT License (Copyright © 2023 Aryan Amit Barsainyan)

---

## 1. Executive Summary

AirGuard AI incorporates molecular odor prediction to map chemical structure representations (**SMILES**) into human perceptual sensory descriptors (e.g., *fruity, alliaceous, sweet, woody*).

This audit documents the technical and architectural status of the molecular odor prediction pipeline, providing complete transparency regarding:
1. The **active production baseline**: Morgan-Fingerprint Multi-Output Random Forest (RDKit).
2. The **OpenPOM Message Passing Neural Network (MPNN)**: dependency constraints, Git LFS checkpoint requirements, and containerization architecture.
3. Strict non-misrepresentation compliance (Rule: *Never label Random Forest as OpenPOM*).

---

## 2. Active Model: Morgan-FP Random Forest Baseline

### 2.1 Model Specifications
- **Model Name:** `Morgan-FP Random Forest Baseline (RDKit Multi-Output)`
- **Version:** `2.0.0`
- **File Checkpoint:** `services/ml_molecular/models/pom_rf_checkpoint.joblib`
- **Input Featurization:** 1024-bit Morgan circular fingerprints (radius=2, equivalent to ECFP4) generated via RDKit `rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)`.
- **Classification Engine:** `sklearn.ensemble.RandomForestClassifier(n_estimators=100, max_depth=20, class_weight='balanced_subsample')`.
- **Inference Latency:** **< 8 ms** on a single CPU core.
- **Runtime Dependencies:** `rdkit`, `scikit-learn`, `numpy` (Zero heavy C++ graph framework dependencies).

### 2.2 Leakage-Free Scaffold Evaluation
- **Dataset:** 4,983 molecules from `curated_GS_LF_merged_4983.csv` (GoodScents & Leffingwell merged corpus).
- **Split Protocol:** Bemis-Murcko Scaffold Split (`rdkit.Chem.Scaffolds.MurckoScaffold`).
- **Partitions:** 2,747 training molecules / 2,236 held-out test molecules (Zero scaffold sharing).
- **Test Macro ROC-AUC:** **0.6648** across 62 evaluated descriptors with $\ge 100$ positive instances.
- **Top Perceptual Descriptors:**
  - `alliaceous`: **0.9014**
  - `onion`: **0.8726**
  - `garlic`: **0.8647**
  - `aldehydic`: **0.8452**
  - `sulfurous`: **0.8422**
  - `fruity`: **0.7860**

---

## 3. OpenPOM MPNN Feasibility & Reproducibility Audit

### 3.1 Architecture Overview
The Principal Odor Map (OpenPOM) model (based on Lee et al., *A Principal Odor Map Unifies Diverse Tasks in Human Olfactory Perception*, Science 2023) implements an MPNN graph neural network:
- Featurizes molecules as 2D/3D graphs (atoms as nodes with hybridization, charge, aromaticity; bonds as edges).
- Executes iterative message-passing graph convolutions across node neighborhoods.
- Pools graph embeddings using `Set2Set` readouts into a 138-dimensional perceptual descriptor output.

### 3.2 Dependency & Compatibility Bottlenecks
Attempting to run OpenPOM natively in modern environments encounters significant friction:
1. **DGL & DGL-Life Dependency:**  
   OpenPOM relies on `dgl` (Deep Graph Library) and `dgllife`. DGL maintains complex C++ binary extensions that lack pre-compiled wheels for Python 3.11+ on macOS ARM64 (Apple Silicon). Installing DGL requires legacy PyTorch ABIs or compiling from source with CMake/OpenMP.
2. **DeepChem Version Coupling:**  
   OpenPOM is built on `deepchem==2.7.x`, which requires specific legacy versions of `numpy (<2.0)` and `torch (<2.1)`. Modern Python environments running NumPy 2.x experience binary incompatibility.
3. **Git LFS Checkpoint Distribution:**  
   Pretrained model weights in `openpom/models/ensemble_models/` (`checkpoint2.pt`, 25.1 MB each) are stored as Git LFS pointers. A standard `git clone` downloads only 133-byte text pointers unless `git-lfs` is configured.

---

## 4. Architectural Comparison Table

| Attribute | Implemented Baseline | OpenPOM MPNN |
|---|---|---|
| **Underlying Model** | Multi-Output Random Forest (100 trees, d=20) | Message Passing Neural Network (MPNN) |
| **Input Representation** | 1024-bit Morgan Fingerprint ($r=2$) | 2D/3D Molecular Graph (Atoms + Bonds) |
| **Test Set Macro ROC-AUC** | **0.6648** (Scaffold Split Verified) | **0.8850** (Published cross-validation) |
| **Stereochemistry** | Flat circular substructure bits | Conformation & spatial stereo message-passing |
| **Platform Compatibility** | 100% cross-platform (macOS ARM64, Linux, Windows) | Linux x86_64 recommended (containerized) |
| **Inference Overhead** | Lightweight, sub-10ms CPU execution | Heavier graph tensor batching (~120ms) |
| **Active in UI** | **YES (Primary Active Model)** | **Comparative Benchmark Reference** |

---

## 5. Isolated Container Roadmap for OpenPOM

In accordance with `AGENTS.md` (*"ML environments: OpenPOM/RDKit/DeepChem in an isolated virtual environment. Core app must work without them"*), OpenPOM is designed as an optional microservice running in an isolated Linux container:

```dockerfile
# Dockerfile.openpom (Isolated Worker)
FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git git-lfs curl && rm -rf /var/lib/apt/lists/

WORKDIR /opt/openpom
RUN git clone --depth 1 https://github.com/biomachinelearning/openpom.git . && \
    git-lfs pull

RUN pip install --no-cache-dir \
    torch==2.0.1 \
    dgl==1.1.2 -f https://data.dgl.ai/wheels/repo.html \
    dgllife==0.3.2 \
    deepchem==2.7.1 \
    rdkit==2023.03.3 \
    fastapi uvicorn

COPY services/ml_molecular/worker.py .
CMD ["uvicorn", "worker:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 6. Dataset Provenance & Licensing Terms

- **OpenPOM Code:** MIT License (Copyright © 2023 Aryan Amit Barsainyan / BioMachineLearning). Permits academic, open-source, and commercial adaptation with attribution.
- **GoodScents & Leffingwell Sensory Compilations:** Academic research use only. AirGuard AI does not distribute proprietary commercial sensory databases; users train on open curated subsets.
- **Safety Compliance:** Odor predictions are strictly perceptual descriptors and must **never** be equated with chemical assays or hazardous gas detection.
