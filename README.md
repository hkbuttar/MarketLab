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

## Research results

The current full-history, net-of-modeled-cost backtests produced the following
results. These are research observations, not expected returns or investment
recommendations.

| Strategy | Period | Net CAGR | Sharpe | Maximum drawdown | Robustness |
| --- | --- | ---: | ---: | ---: | ---: |
| Momentum | 2000–2026 | 4.32% | 0.27 | -63.18% | 34.4/100, weak |
| Low volatility | 2000–2026 | 9.85% | 0.75 | -43.26% | 66.2/100, moderate |
| Quality, value, momentum | 2009–2026 | 13.39% | 0.77 | -42.36% | 69.9/100, moderate |

The stricter shared out-of-sample comparison ran from January 2018 through June
2026 with identical selection, turnover, and cost assumptions:

| Model or baseline | Net CAGR | Sharpe | Maximum drawdown |
| --- | ---: | ---: | ---: |
| SPY | 14.24% | 0.71 | -19.78% |
| Quality, value, momentum | 11.77% | 0.52 | -32.23% |
| Gradient boosting | 8.78% | 0.40 | -27.31% |
| Random forest | 8.17% | 0.37 | -26.61% |
| Elastic Net | 8.14% | 0.38 | -26.72% |

The tested ML models did not add out-of-sample value over the simple multi-factor
baseline or SPY. Full methodology, negative findings, regime behavior, capacity,
and limitations are documented in the flagship studies below. Current sector
labels are not historically effective GICS classifications, and daily modeled
execution cannot reproduce intraday liquidity or live fills.

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

With raw provider downloads already present, inspect the complete resumable
research workflow before running it:

```bash
python scripts/run_research_pipeline.py --dry-run
```

Completed artifacts are skipped, so the same command without `--dry-run` resumes
from the first missing task. Use `--start-at` and `--through` to run an inclusive
stage range from `data`, `features`, `research`, `validation`, `ml`, and
`reporting`. Each real run writes a manifest under `experiments/pipeline_runs/`.

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

## Flagship research studies

The published studies use persisted MarketLab results and state negative as well
as positive findings:

- [Momentum](docs/studies/flagship-momentum.md)
- [Low volatility](docs/studies/flagship-low-volatility.md)
- [Quality, value, and momentum](docs/studies/flagship-quality-value-momentum.md)
- [Machine learning](docs/studies/flagship-machine-learning.md)

Regenerate all Markdown and HTML studies after rebuilding research artifacts:

```bash
python scripts/generate_flagship_studies.py
```

## Documentation

- [System architecture](docs/system-architecture.md)
- [Repository architecture](docs/repository-architecture.md)
- [Data methodology](docs/data-methodology.md)
- [Canonical schemas](docs/data-schemas.md)
- [Data acquisition and processing](docs/data-downloads.md)
- [Factor research](docs/factor-research.md)
- [Backtesting methodology](docs/backtesting-methodology.md)
- [ML validation](docs/ml-validation.md)
- [Testing](docs/testing.md)
- [Performance and laptop resource budget](docs/performance.md)
- [User guide](docs/user-guide.md)

## License

MarketLab is available under the [MIT License](LICENSE).
