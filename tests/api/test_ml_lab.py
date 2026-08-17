"""Tests for persisted ML Lab aggregation."""

import json

from fastapi.testclient import TestClient

import backend.api.routers.models as models_router
from backend.api.app import app
from backend.services.ml_lab import ml_lab_result

client = TestClient(app)


def _artifacts(root) -> None:
    directory = root / "reports/ml/explainability"
    directory.mkdir(parents=True)
    metrics = {
        "months": 12,
        "mean_rank_ic": 0.04,
        "positive_ic_fraction": 0.6,
        "net_cagr": 0.08,
        "benchmark_cagr": 0.1,
        "oos_sharpe": 0.5,
        "maximum_drawdown": -0.2,
        "average_turnover": 0.3,
        "annualized_cost_drag": 0.004,
    }
    (root / "reports/ml/model_evaluation.json").write_text(
        json.dumps(
            {
                "method": "purged OOS",
                "transaction_cost_bps_per_one_way_turnover": 10,
                "models": {"elastic_net": metrics},
            }
        )
    )
    (directory / "feature_importance_stability.json").write_text(
        json.dumps(
            {
                "method": "permutation and SHAP",
                "models": {
                    "elastic_net": {
                        "momentum": {
                            "mean_permutation_importance": 0.02,
                            "mean_absolute_shap": 0.01,
                            "top_three_year_fraction": 0.75,
                        }
                    }
                },
            }
        )
    )
    (root / "reports/ml/walk_forward_purging_comparison.json").write_text(
        json.dumps({"models": {"elastic_net": {"delta_mean_monthly_ic": 0.001}}})
    )


def test_ml_lab_aggregates_evaluation_and_explainability(tmp_path) -> None:
    _artifacts(tmp_path)

    result = ml_lab_result(tmp_path)

    assert result.models[0].name == "elastic_net"
    assert result.models[0].top_features[0].name == "momentum"
    assert result.models[0].purging_delta_ic == 0.001


def test_models_endpoint_returns_typed_diagnostics(tmp_path, monkeypatch) -> None:
    _artifacts(tmp_path)
    monkeypatch.setattr(models_router, "ml_lab_result", lambda: ml_lab_result(tmp_path))

    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json()["models"][0]["oos_sharpe"] == 0.5
