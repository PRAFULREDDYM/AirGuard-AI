# Contributing to AirGuard AI

Thank you for your interest in contributing to AirGuard AI.

## Core Development Principles

1. **Safety First**: Never modify the 14 safety invariants to bypass life-safety constraints, rate limits, or fire/gas leak interlocks.
2. **Scientific Honesty**: Never misrepresent statistical electronic-nose classifications as verified chemical assays or medical-grade detection. Keep molecular models decoupled from ambient sensor telemetry.
3. **Local-First & Privacy**: Avoid adding mandatory third-party cloud dependencies or tracking telemetry.

## Development Workflow

1. Fork and clone the repository.
2. Set up Python 3.11 virtual environment and Node.js 20.
3. Install backend dependencies:
   ```bash
   pip install -r services/api/requirements.txt
   pip install -r services/ml_molecular/requirements.txt
   pip install -r services/ml_environment/requirements.txt
   ```
4. Install web dependencies:
   ```bash
   cd apps/web && npm install
   ```
5. Run the test suite before submitting PRs:
   ```bash
   PYTHONPATH=. pytest tests/unit/ tests/integration/
   cd apps/web && npm run build
   ```

## Commit Standards

Follow conventional commits:
- `feat(...)`: New capability or integration adapter
- `fix(...)`: Bug correction or invariant fix
- `docs(...)`: Documentation updates
- `test(...)`: Unit, integration, or browser E2E tests

