# Changelog

All notable MarketLab releases are documented here. Versions follow semantic
versioning.

## 1.0.0 — 2026-08-16

First complete research-platform release.

### Added

- Point-in-time daily U.S. equity and fundamental data pipelines with validation
  and canonical Parquet storage.
- Technical and fundamental feature engines, factor diagnostics, and five
  strategy families.
- Daily portfolio simulation with constraints, turnover controls, transaction
  costs, market impact, accounting, and capacity analysis.
- Performance, risk, attribution, exposure, regime, parameter-sensitivity,
  bootstrap, and multiple-testing diagnostics.
- Purged expanding-window ML research with Elastic Net, random forest, gradient
  boosting, explainability, and simple-strategy comparisons.
- Reproducible experiment manifests, flagship Markdown and HTML studies, and a
  resumable end-to-end research pipeline.
- FastAPI, PostgreSQL, Next.js dashboards, Docker Compose, reproducible UI
  screenshots, and Python/frontend continuous integration.

### Known limitations

- Current sector labels are not historically effective GICS classifications.
- The platform models daily long-only U.S. equity research, not live execution.
- Historical results and validation diagnostics do not imply future returns.
