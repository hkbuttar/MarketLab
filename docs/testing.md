# Testing and quality checks

The test suite covers canonical schemas, download behavior, temporal integrity,
feature construction, factor statistics, portfolio constraints, accounting,
execution costs, analytics, attribution, regimes, robustness, walk-forward ML,
API contracts, reporting, and deployment configuration.

Run the complete local checks:

```bash
source .venv/bin/activate
python -m pytest -q
python -m ruff check .
python -m black --check .
cd frontend
npm run typecheck
npm run build
```

Validate the deployment definition without expanding secrets into output:

```bash
docker compose config --quiet
```

Tests use temporary artifacts when behavior depends on files. API tests must not
depend on a developer’s local research outputs. Warnings from external packages
are reported but are not suppressed unless their cause is understood.

Performance claims require a measured command, dataset, machine description,
elapsed time, and peak memory. Do not infer scalability from unit-test runtime.
