from pathlib import Path

import pytest

from backend.services.dashboard import dashboard_summary


def test_dashboard_aggregates_existing_research_artifacts() -> None:
    summary = dashboard_summary(Path("."))

    assert summary.best_oos_model == "gradient_boosting"
    assert summary.best_oos_sharpe == pytest.approx(0.3951309324)
    assert summary.average_robustness_score == pytest.approx(56.8239778553)
    assert summary.factor_research[0].name == "volatility_63"
    assert summary.recent_reports


def test_dashboard_handles_an_empty_project(tmp_path: Path) -> None:
    summary = dashboard_summary(tmp_path)

    assert summary.best_oos_model is None
    assert summary.best_oos_sharpe is None
    assert summary.average_robustness_score is None
    assert summary.factor_research == []
    assert summary.recent_experiments == []
    assert summary.recent_reports == []
