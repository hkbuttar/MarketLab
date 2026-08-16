"""Replay gross strategy paths across fixed all-in cost assumptions."""

from pathlib import Path

from marketlab.validation.sensitivity import run_cost_sensitivity


def main() -> int:
    rows = run_cost_sensitivity(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/validation/sensitivity"),
    )
    for row in rows:
        print(
            row["strategy"],
            f"cost={row['cost_bps']}bps",
            f"CAGR={row['cagr']:.2%}",
            f"Sharpe={row['sharpe']:.2f}",
            f"attractive={row['economically_attractive']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
