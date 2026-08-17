import json
from pathlib import Path

import pytest

from backend.services.dashboard import dashboard_summary


def test_dashboard_aggregates_research_artifacts(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "reports/ml/comparison/model_strategy_comparison.json",
        {
            "results": {
                "elastic_net": {"category": "ml_model", "sharpe": 0.3},
                "gradient_boosting": {"category": "ml_model", "sharpe": 0.4},
                "momentum": {"category": "simple_strategy", "sharpe": 0.5},
            }
        },
    )
    _write_json(
        tmp_path / "reports/validation/robustness_scores.json",
        {
            "strategies": {
                "momentum": {"overall_score": 40},
                "low_volatility": {"overall_score": 60},
            }
        },
    )
    _write_json(
        tmp_path / "reports/factors/tear_sheet_summary.json",
        {
            "information_coefficient": {
                "momentum_12_1": {"mean": 0.02},
                "volatility_63": {"mean": -0.04},
            }
        },
    )
    _write_json(
        tmp_path / "experiments/comparison/run-1.json",
        {
            "run_id": "run-1",
            "experiment": "comparison",
            "created_at": "2026-01-01T00:00:00Z",
        },
    )

    summary = dashboard_summary(tmp_path)

    assert summary.best_oos_model == "gradient_boosting"
    assert summary.best_oos_sharpe == pytest.approx(0.4)
    assert summary.average_robustness_score == pytest.approx(50)
    assert summary.factor_research[0].name == "volatility_63"
    assert summary.recent_experiments[0].experiment_id == "run-1"
    assert summary.recent_reports


def test_dashboard_handles_an_empty_project(tmp_path: Path) -> None:
    summary = dashboard_summary(tmp_path)

    assert summary.best_oos_model is None
    assert summary.best_oos_sharpe is None
    assert summary.average_robustness_score is None
    assert summary.factor_research == []
    assert summary.recent_experiments == []
    assert summary.recent_reports == []


def test_dashboard_ignores_invalid_experiment_artifacts(tmp_path: Path) -> None:
    experiment_root = tmp_path / "experiments/comparison"
    experiment_root.mkdir(parents=True)
    (experiment_root / "corrupt.json").write_bytes(b"\xa3not UTF-8")
    (experiment_root / "._metadata.json").write_bytes(b"\xa3macOS metadata")
    _write_json(
        experiment_root / "run-1.json",
        {
            "run_id": "run-1",
            "experiment": "comparison",
            "created_at": "2026-01-01T00:00:00Z",
        },
    )

    summary = dashboard_summary(tmp_path)

    assert [item.experiment_id for item in summary.recent_experiments] == ["run-1"]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
