"""Compare ML models and simple strategies under shared portfolio rules."""

from pathlib import Path

from marketlab.ml.comparison import compare_models_with_strategies


def main() -> int:
    report = compare_models_with_strategies(
        Path("data/features/ml/walk_forward_predictions_purged.csv.gz"),
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("reports/ml/monthly_model_performance.csv"),
        Path("reports/ml/comparison"),
    )
    for name in report["ranking_by_net_cagr"]:
        values = report["results"][name]
        print(
            name,
            f"CAGR={values['net_cagr']:.2%}",
            f"Sharpe={values['sharpe']:.2f}",
            f"MaxDD={values['maximum_drawdown']:.2%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
