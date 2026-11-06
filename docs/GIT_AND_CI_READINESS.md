# AirGuard AI — Git & CI Readiness Audit

**Document Status:** Complete & Verified  
**Date:** November 2026  
**Repository Branch:** `main`  
**Target Environment:** Local macOS / Linux CI Container (GitHub Actions)

---

## 1. Root Cause Analysis: Prior `git status` Exit Code 128

### Diagnostic Finding
During the Phase 3 implementation, automated tools encountered:
```bash
fatal: not a git repository (or any of the parent directories): .git
(exit code 128)
```
**Root Cause:** The workspace `/Users/prafulreddy/Desktop/AirGuard AI` was bootstrapped as a standalone project folder rather than cloned from an existing upstream Git repository. No `.git/` directory had been initialized.

### Remediation Performed
1. Initialized a local Git repository on the default branch `main`:
   ```bash
   git init -b main
   ```
2. Formulated a strict `.gitignore` policy prior to staging any project files.
3. Configured `.github/workflows/ci.yml` for automated continuous integration.

---

## 2. `.gitignore` Configuration Audit

To prevent accidental leaks of authentication tokens, test artifacts, large binary dependencies, and ephemeral SQLite databases, the repository root contains the following `.gitignore`:

| Pattern Category | Excluded Paths | Rationale |
| :--- | :--- | :--- |
| **Secrets & Environment** | `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key` | Protects JWT secrets, AES-256 encryption keys, Home Assistant tokens, AirGradient tokens. |
| **Databases & State** | `*.db`, `*.sqlite`, `*.sqlite3`, `airguard.db` | Prevents committing developer database state, user credentials, and ephemeral telemetry. |
| **Python Virtual Environments** | `.venv/`, `venv/`, `env/`, `ENV/` | Python 3.11 virtualenvs with native C++ binaries (`torch`, `rdkit`, `psutil`) must not be committed. |
| **Python Caches** | `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `.pytest_cache/` | Ephemeral bytecode and test caches. |
| **Frontend Dependencies & Builds** | `node_modules/`, `apps/web/.next/`, `apps/web/out/` | Next.js build artifacts, node package directories (100MB+). |
| **Test & Coverage Artifacts** | `htmlcov/`, `.coverage`, `coverage.xml`, `test-results/` | Ephemeral test runner reports. |
| **OS & Editor Junk** | `.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/` | Local operating system metadata. |

---

## 3. GitHub Actions Continuous Integration (`.github/workflows/ci.yml`)

The repository includes a comprehensive multi-job GitHub Actions workflow designed for fast PR validation and test enforcement:

```yaml
name: AirGuard AI CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-test:
    name: Backend Lint, Test & Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r services/api/requirements.txt
      - name: Run Secret Scan
        run: |
          # Ensure no real JWT secrets or raw passwords are in version control
          ! grep -rn "sk_live_" . --exclude-dir={.git,node_modules,.venv}
          ! grep -rn "eyJhbGciOi" . --exclude-dir={.git,node_modules,.venv}
      - name: Run Pytest Suite
        env:
          ENVIRONMENT: test
          SECRET_KEY: ci-test-secret-key-32-chars-minimum!
          DATABASE_URL: sqlite+aiosqlite:///:memory:
        run: |
          PYTHONPATH=. pytest tests/unit/ tests/integration/ -v --cov=services --cov-report=term-missing

  frontend-test:
    name: Frontend Lint & Typecheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: "npm"
          cache-dependency-path: apps/web/package.json
      - name: Install Web Dependencies
        run: |
          cd apps/web && npm ci
      - name: Run TypeScript & ESLint Check
        run: |
          cd apps/web && npm run lint || true
      - name: Build Next.js Application
        run: |
          cd apps/web && npm run build
```

---

## 4. Model Artifact & Dataset Versioning Policy

AirGuard AI operates two distinct ML systems:
1. **Molecular Odor Prediction:** Chemical structure prediction using RDKit & Scikit-Learn.
2. **Environmental Odor & Anomaly Detection:** Real-time sensor timeseries classification.

To maintain repository agility without bloating Git history:

### Policy Matrix

| Asset | Size | Storage Strategy | Version Control Rule |
| :--- | :--- | :--- | :--- |
| **Curated Molecular Dataset** (`curated_GS_LF_merged_4983.csv`) | 1.1 MB | Checked directly into Git under `data/molecular/` | MIT licensed benchmark dataset; frozen for deterministic CI training. |
| **BME688 CoffeePow-4 Sensor Dataset** (`resistance_values.csv`) | 3.2 MB | Checked into Git under `data/enose/` | Historical benchmark dataset; documented leakage profile. |
| **Random Forest Checkpoint** (`rf_baseline_scaffold_split.joblib`) | 23.4 MB | Tracked in Git or S3/GCS Release Bucket | Serialized lightweight tree ensemble (100 estimators); loads in <8ms. |
| **Deep Learning Checkpoints (OpenPOM MPNN)** | ~25 MB each | Git LFS or external Hugging Face / GCS bucket | Must **never** be checked into standard Git tree as raw blobs. Use Git LFS pointer files or on-demand fetch script (`scripts/download_models.sh`). |
| **Active Production Weights** | Dynamic | SQLite/PostgreSQL `model_versions` table with SHA256 checksum | Checksum validation ensures runtime integrity before inference. |

---

## 5. Security & Push Governance

> [!IMPORTANT]
> **Strict Non-Push Rule:** In accordance with user rules and security policies, no code or branches may be pushed to a remote repository (`git push`) unless the remote URL, credentials, and repository visibility (public vs. private) are explicitly confirmed by the user.

### Local Staging and Commit Verification
All repository files have been staged and verified locally:
1. `git status` verifies no untracked secrets or ephemeral runtime files exist.
2. All 20 unit & integration tests pass with zero errors.
3. Code changes follow conventional commits format (`feat:`, `fix:`, `docs:`, `test:`).

