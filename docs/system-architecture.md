# System architecture

MarketLab is a modular monolith with three runtime services and one shared
artifact boundary.

```text
Alpha Vantage + SEC EDGAR
          |
          v
  local data artifacts -----> marketlab/ quantitative engine
          |                              |
          |                              v
          +----------------------> reports + experiments
                                         |
                                         v
Next.js dashboard <---- HTTP ---- FastAPI backend ---- PostgreSQL metadata
```

## Runtime responsibilities

- `marketlab/` owns data processing, features, strategies, portfolio logic,
  backtesting, analytics, validation, ML, experiments, and report rendering.
- `backend/` validates requests and exposes engine results. It does not duplicate
  quantitative definitions.
- `frontend/` consumes versioned API responses. It does not calculate investment
  metrics from raw market data.
- PostgreSQL stores application and experiment metadata. Large time series stay
  in compressed CSV, Parquet, or JSON artifacts.

Docker Compose runs PostgreSQL, FastAPI, and Next.js. Local `data/`,
`experiments/`, and `reports/` directories are mounted into the backend so images
remain small and contain no licensed or private datasets.

## Trust boundaries

Provider responses are immutable raw inputs. Canonical loaders normalize them,
validation reports disclose rejected or suspicious records, and point-in-time
joins prevent future filings from entering historical features. The API reads
persisted research artifacts and returns typed schemas. Report and experiment
paths are root-bounded before files are opened.

## Scope boundary

The application supports daily, long-only U.S. equity research. It is not a live
trading, brokerage, intraday, derivative, or multi-user SaaS platform.
