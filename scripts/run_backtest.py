"""Run daily gross and net strategy valuation from monthly targets."""

from pathlib import Path

from marketlab.backtest import run_daily_backtest


def main() -> int:
    result = run_daily_backtest(
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/processed/prices/prices_clean.csv.gz"),
        Path("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz"),
        Path("data/processed/reference/security_crosswalk.csv.gz"),
        Path("data/features/backtests/daily_results.csv"),
    )
    for strategy, summary in result.items():
        print(strategy, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
