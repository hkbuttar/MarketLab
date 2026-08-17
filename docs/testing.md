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

GitHub Actions runs two independent required-quality jobs on pushes and pull
requests to `main`. The Python job installs the package and runs Black, Ruff, and
pytest. The frontend job uses Node.js 22 with `npm ci`, then runs TypeScript
checking and a production Next.js build. Superseded runs on the same branch are
cancelled to avoid wasting CI capacity.
