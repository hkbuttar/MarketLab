# User guide

## Start locally

```bash
source .venv/bin/activate
uvicorn backend.api.app:app --reload
```

In a second terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`. For the containerized demo, follow the Docker
instructions in the repository README.

## Product pages

- **Overview** summarizes current research artifacts.
- **Factor Lab** explores IC, quantiles, turnover, correlations, and sectors.
- **Capacity** shows deployable AUM and participation/cost curves.
- **Strategies** submits canonical backtests and polls their status.
- **Backtests** lists runs and displays performance, risk, benchmark, and costs.
- **ML Lab** compares purged walk-forward models and feature importance.
- **Experiments** exposes immutable manifests and reproduction metadata.
- **Compare** evaluates two to five completed backtests side by side.
- **Reports** catalogs artifacts and generates Markdown/HTML backtest studies.

## Typical workflow

1. Generate or update canonical data and feature artifacts with scripts.
2. Review validation and Factor Lab evidence.
3. Select a registered strategy and submit a backtest.
4. Inspect the completed result, capacity, robustness, and comparison pages.
5. Generate a research report.
6. Record serious research runs and verify them with
   `python scripts/reproduce_experiment.py RUN_ID --verify-only`.

The Strategy Builder changes dates, starting capital, and display cost
assumptions. Portfolio signal and constraint definitions are engine-owned and
require rebuilding canonical targets when changed.
