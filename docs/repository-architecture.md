# Repository architecture

```text
marketlab/     Quantitative engine; no web-framework dependency
backend/       FastAPI routers, response schemas, services, database metadata
frontend/      Next.js App Router dashboard
data/          Raw, processed, feature, portfolio, and backtest artifacts
experiments/   Immutable manifests with hashes and git state
reports/       Validation, analytics, ML, and generated studies
scripts/       Explicit pipeline entry points
tests/         Unit, integration, API, and deployment-contract tests
docker/        Backend and frontend image definitions
docs/          Focused operating and methodology documentation
```

Dependencies flow toward the engine: the backend imports `marketlab`, and the
frontend calls the backend. Quantitative code must not import FastAPI, React, or
database models. Time-series artifacts are not copied into PostgreSQL.

Each pipeline script has explicit input and output paths. Large writers use
`.part` files and atomic replacement so interruption cannot create a seemingly
complete artifact. Serious research runs record the command, parameters, git
revision, inputs, outputs, sizes, and SHA-256 fingerprints under `experiments/`.

Provider-specific names stop at downloader and loader boundaries. Downstream
modules consume the canonical schemas documented in [data-schemas.md](data-schemas.md).
