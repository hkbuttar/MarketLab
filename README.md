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

The repository foundation, automated quality checks, and Python package
boundaries are in place. Domain modules intentionally contain no implementation
yet; development follows the data-to-report dependency order described in the
project blueprint.

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
