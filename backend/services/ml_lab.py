"""Aggregate persisted ML evaluation and explainability artifacts."""

import json
from pathlib import Path
from typing import Any

from backend.schemas.ml_lab import (
    FeatureImportance,
    MLLabResponse,
    MLModelDiagnostics,
)


def ml_lab_result(project_root: Path = Path(".")) -> MLLabResponse:
    root = project_root.resolve()
    evaluation = _read(root / "reports/ml/model_evaluation.json")
    explanation = _read(
        root / "reports/ml/explainability/feature_importance_stability.json"
    )
    purging = _read(root / "reports/ml/walk_forward_purging_comparison.json")
    models = []
    for name, metrics in sorted(evaluation["models"].items()):
        importance = explanation.get("models", {}).get(name, {})
        leaders = sorted(
            importance.items(),
            key=lambda item: float(item[1]["mean_permutation_importance"]),
            reverse=True,
        )[:5]
        purging_metrics = purging.get("models", {}).get(name, {})
        models.append(
            MLModelDiagnostics(
                name=name,
                months=metrics["months"],
                mean_rank_ic=metrics["mean_rank_ic"],
                positive_ic_fraction=metrics["positive_ic_fraction"],
                net_cagr=metrics["net_cagr"],
                benchmark_cagr=metrics["benchmark_cagr"],
                oos_sharpe=metrics["oos_sharpe"],
                maximum_drawdown=metrics["maximum_drawdown"],
                average_turnover=metrics["average_turnover"],
                annualized_cost_drag=metrics["annualized_cost_drag"],
                purging_delta_ic=purging_metrics.get("delta_mean_monthly_ic"),
                top_features=[
                    FeatureImportance(
                        name=feature,
                        permutation_importance=values["mean_permutation_importance"],
                        mean_absolute_shap=values["mean_absolute_shap"],
                        top_three_year_fraction=values["top_three_year_fraction"],
                    )
                    for feature, values in leaders
                ],
            )
        )
    return MLLabResponse(
        method=evaluation["method"],
        explainability_method=explanation.get("method", "unavailable"),
        transaction_cost_bps=evaluation["transaction_cost_bps_per_one_way_turnover"],
        models=models,
    )


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
