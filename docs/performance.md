# Performance and laptop resource budget

MarketLab's primary execution target is a CPU-only research laptop processing
hundreds of U.S. securities over 10–15 years of daily history. Large parameter
grids and model families run sequentially. Intraday data, neural networks, and
claims about institutional-scale throughput are outside this budget.

Run the representative, bounded suite with:

```bash
python scripts/benchmark_pipeline.py
```

It measures full monthly-panel loading, technical feature generation for 25 real
symbols, one momentum backtest from 2016 through 2025, and a 250-iteration
moving-block bootstrap. Each workload runs in a fresh process, and the report at
`reports/performance/pipeline_benchmark.json` records wall-clock duration and
peak resident memory alongside machine metadata.

The walk-forward Elastic Net fit and full parameter-sensitivity grid are more
expensive and therefore opt-in:

```bash
python scripts/benchmark_pipeline.py --include-expensive
```

Run one workload with repeated `--workload` flags when profiling a regression.
Results are measurements of the current datasets and machine, not scalability
guarantees. Feature-generation timing includes extracting its 25-symbol sample;
the ML benchmark uses only Elastic Net with test folds beginning in 2025; and the
bootstrap benchmark uses 250 rather than the production default of 1,000 draws.

## Reference measurement

The bounded suite was measured on August 16, 2026, on a 14-logical-core Apple
Silicon Mac running Python 3.14.2:

| Workload | Measured scope | Time | Peak RSS |
| --- | --- | ---: | ---: |
| Data load | 777,652 panel rows | 1.79 s | 194.8 MiB |
| Feature generation | 48,644 rows, 25 symbols | 1.71 s | 195.8 MiB |
| Backtest | Momentum, 2016–2025 | 65.13 s | 407.6 MiB |
| Bootstrap | 3 strategies, 250 draws | 1.26 s | 210.5 MiB |

The JSON report is the authoritative full-precision record. Re-run the harness
after material pipeline or dataset changes rather than treating this snapshot as
a fixed performance target.
