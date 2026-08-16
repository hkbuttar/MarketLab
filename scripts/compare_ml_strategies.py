"""Compare ML models and simple strategies under shared portfolio rules."""

from pathlib import Path

from marketlab.experiments import record_experiment
from marketlab.ml.comparison import compare_models_with_strategies


def main() -> int:
    predictions = Path("data/features/ml/walk_forward_predictions_purged.csv.gz")
    targets = Path("data/features/portfolios/monthly_targets.csv.gz")
    panel = Path("data/features/factors/monthly_panel_investable.csv.gz")
    monthly = Path("reports/ml/monthly_model_performance.csv")
    output_directory = Path("reports/ml/comparison")
    report = compare_models_with_strategies(
        predictions,
        targets,
        panel,
        monthly,
        output_directory,
    )
    manifest = record_experiment(
        "ml_strategy_comparison",
        command="python scripts/compare_ml_strategies.py",
        parameters=report["constraints"],
        inputs=[predictions, targets, panel, monthly],
        outputs=[
            output_directory / "model_strategy_monthly_comparison.csv",
            output_directory / "model_strategy_comparison.json",
        ],
        metrics={name: values for name, values in report["results"].items()},
    )
    for name in report["ranking_by_net_cagr"]:
        values = report["results"][name]
        print(
            name,
            f"CAGR={values['net_cagr']:.2%}",
            f"Sharpe={values['sharpe']:.2f}",
            f"MaxDD={values['maximum_drawdown']:.2%}",
        )
    print(f"Experiment manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
