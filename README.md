# MarketLab — Quantitative Research, Backtesting & Strategy Validation Platform
MarketLab is a full-stack quantitative research platform for factor analysis,
systematic strategy construction, realistic portfolio backtesting,
transaction-cost and capacity modeling, factor attribution, regime analysis,
walk-forward machine learning, robustness testing, and reproducible reporting on
daily U.S. equities.

The platform is research infrastructure—not a live-trading system. Its purpose is
to take an investment hypothesis from raw data through point-in-time feature
engineering, portfolio simulation, out-of-sample validation, and a reproducible
research report without rebuilding the stack for every strategy.

## Status

MarketLab now includes the quantitative research engine, point-in-time data
pipeline, factor and strategy research, realistic backtesting, robustness and ML
validation, FastAPI product layer, Next.js dashboard, PostgreSQL metadata schema,
and reproducible reports. Development data and generated artifacts remain local
and are mounted into containers rather than copied into images.

## Scope

MarketLab targets daily U.S. equities and benchmark ETFs, technical and
fundamental factors, long-only portfolios, daily simulation, realistic costs,
capacity analysis, robustness testing, walk-forward ML, FastAPI, PostgreSQL,
React, reports, and Docker.

Out of scope are live execution, broker integrations, intraday or tick data,
options, futures, crypto, short-selling infrastructure, order books, news/NLP,
reinforcement learning, distributed compute, Kubernetes, and multi-user SaaS.

## Development setup

MarketLab requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
black --check .
```

PostgreSQL is available for later backend work:

```bash
docker compose up -d postgres
```

## Full local demo with Docker

The container stack runs PostgreSQL, FastAPI, and the Next.js dashboard. Existing
`data/`, `experiments/`, and `reports/` directories are mounted into the backend.

```bash
cp .env.example .env
docker compose config --quiet
docker compose up --build
```

Open:

- Dashboard: `http://localhost:3000`
- API documentation: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

The data-provider API key is unnecessary for browsing existing artifacts or
running backtests. It is required only when explicitly running download scripts.

Stop the application without deleting PostgreSQL data:

```bash
docker compose down
```

The research datasets are intentionally not baked into the images. Populate the
local artifact directories before starting the complete demo.
