"""Adjust strategy Sharpe evidence for the recorded research search breadth."""

from pathlib import Path

from marketlab.validation.deflated_sharpe import run_deflated_sharpe_analysis


def main() -> int:
    report = run_deflated_sharpe_analysis(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/validation/sensitivity/parameter_sensitivity.csv"),
        Path("reports/validation/deflated_sharpe.json"),
    )
    print(f"Recorded trials: {report['number_of_trials']}")
    for strategy, values in report["strategies"].items():
        print(
            strategy,
            f"raw Sharpe={values['raw_sharpe']:.2f}",
            f"adjusted probability={values['deflated_sharpe_probability']:.1%}",
            f"evidence={values['adjusted_evidence']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
