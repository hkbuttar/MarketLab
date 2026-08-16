"""Build the transparent internal MarketLab robustness diagnostic."""

from pathlib import Path

from marketlab.validation.robustness_score import build_robustness_scores


def main() -> int:
    report = build_robustness_scores(
        Path("data/features/backtests/daily_results.csv"),
        Path("reports/validation/sensitivity/cost_sensitivity.csv"),
        Path("reports/validation/sensitivity/parameter_sensitivity.csv"),
        Path("reports/regimes/regime_performance.csv"),
        Path("reports/validation/bootstrap/bootstrap_summary.json"),
        Path("reports/validation"),
    )
    for strategy, values in report["strategies"].items():
        print(strategy, f"score={values['overall_score']:.1f}", values["label"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
