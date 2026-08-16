"""Run purged walk-forward ML and compare it with standard predictions."""

from pathlib import Path

from marketlab.ml.training import run_walk_forward_training
from marketlab.validation.purging import compare_walk_forward_predictions


def main() -> int:
    standard = Path("data/features/ml/walk_forward_predictions.csv.gz")
    purged = Path("data/features/ml/walk_forward_predictions_purged.csv.gz")
    metadata = run_walk_forward_training(
        Path("data/features/ml/cross_sectional_ranking.csv.gz"),
        purged,
        purge_calendar_path=Path("data/features/regimes/daily_regimes.csv"),
    )
    report = compare_walk_forward_predictions(
        standard,
        purged,
        Path("reports/ml/walk_forward_purging_comparison.json"),
    )
    print(f"Wrote {metadata['prediction_rows']:,} purged predictions to {purged}")
    for model, values in report["models"].items():
        print(
            model,
            f"standard IC={values['standard']['mean_monthly_ic']:.4f}",
            f"purged IC={values['purged']['mean_monthly_ic']:.4f}",
            f"delta={values['delta_mean_monthly_ic']:.4f}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
