"""Build performance analytics from daily backtest results."""

import argparse
from pathlib import Path

from marketlab.analytics import build_performance_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.0,
        help="Constant annual risk-free rate as a decimal (default: 0)",
    )
    arguments = parser.parse_args()
    report = build_performance_report(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz"),
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("reports/performance"),
        risk_free_rate=arguments.risk_free_rate,
    )
    for strategy, values in report.items():
        print(
            strategy,
            f"CAGR={values['cagr']:.2%}",
            f"Sharpe={values['sharpe']:.2f}",
            f"MaxDD={values['maximum_drawdown']:.2%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
