"""Evaluate purged out-of-sample ML ranking portfolios."""

from pathlib import Path

from marketlab.ml.evaluation import evaluate_ml_predictions


def main() -> int:
    report = evaluate_ml_predictions(
        Path("data/features/ml/walk_forward_predictions_purged.csv.gz"),
        Path("data/features/regimes/daily_regimes.csv"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/ml"),
    )
    for model, values in report["models"].items():
        print(
            model,
            f"IC={values['mean_rank_ic']:.4f}",
            f"net CAGR={values['net_cagr']:.2%}",
            f"Sharpe={values['oos_sharpe']:.2f}",
            f"MaxDD={values['maximum_drawdown']:.2%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
