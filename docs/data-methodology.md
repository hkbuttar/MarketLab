# Data methodology

MarketLab uses daily U.S. equity and benchmark data from Alpha Vantage, SEC EDGAR
filing metadata and Company Facts, and daily research factors. Raw responses are
retained unchanged; processed datasets use canonical names and types.

## Point-in-time rules

- Fundamentals become usable only after their SEC acceptance timestamp.
- Cross-sectional features at date `t` use records with `available_date <= t`.
- Forward returns are labels for research and ML evaluation, never inputs.
- Portfolio signals execute no earlier than the following trading session.
- Walk-forward folds purge overlapping labels and apply an embargo.

## Universe

The investable universe excludes non-common instruments, test securities,
invalid records, insufficient histories, and observations below the configured
liquidity threshold. Membership is recomputed through time; today’s constituents
are not projected backward.

## Storage

Raw provider snapshots live under `data/raw/`. Canonical processed datasets and
Parquet mirrors live under `data/processed/`. Features, portfolio targets, trades,
and backtests live under `data/features/`. Dataset artifacts are Git-ignored.

Historically effective GICS classifications remain a licensed-data gap. Current
sector labels may support descriptive analysis, but results disclose that they
are not point-in-time classifications.

See [data-downloads.md](data-downloads.md) for commands and
[data-schemas.md](data-schemas.md) for field contracts.
