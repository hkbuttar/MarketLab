"""Run seeded moving-block bootstrap strategy robustness analysis."""

from pathlib import Path

from marketlab.validation.bootstrap import run_bootstrap_analysis


def main() -> int:
    report = run_bootstrap_analysis(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/validation/bootstrap"),
    )
    for strategy, values in report["strategies"].items():
        print(
            strategy,
            f"median Sharpe={values['sharpe']['median']:.2f}",
            f"P(Sharpe>0)={values['probability_sharpe_positive']:.1%}",
            f"P(CAGR>SPY)={values['probability_cagr_above_benchmark']:.1%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
