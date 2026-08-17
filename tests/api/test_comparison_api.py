"""Tests for cross-experiment comparisons."""

import pytest
from fastapi.testclient import TestClient

import backend.services.comparison as service
from backend.api.app import app

client = TestClient(app)


def _result(experiment_id: str) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "strategy": "momentum",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "metrics": {
            "total_return": 0.5,
            "benchmark_return": 0.4,
            "cagr": 0.09,
            "annualized_volatility": 0.15,
            "sharpe": 0.6,
            "maximum_drawdown": -0.2,
            "total_costs": 1000,
            "cost_drag": 0.01,
            "observations": 1000,
        },
        "equity_curve": [],
    }


def test_comparison_flags_inconsistent_cost_assumptions(monkeypatch) -> None:
    monkeypatch.setattr(service, "read_backtest_result", _result)
    monkeypatch.setattr(
        service,
        "read_backtest_job",
        lambda experiment_id: {
            "request": {"cost_bps": 5 if experiment_id == "one" else 10}
        },
    )

    result = service.compare_backtests(["one", "two"])

    assert len(result.experiments) == 2
    assert any(
        "transaction-cost" in warning for warning in result.configuration_warnings
    )


def test_comparison_requires_two_to_five_unique_experiments() -> None:
    with pytest.raises(ValueError, match="2 and 5"):
        service.compare_backtests(["one"])
    with pytest.raises(ValueError, match="unique"):
        service.compare_backtests(["one", "one"])


def test_comparison_endpoint_validates_selection() -> None:
    response = client.get("/api/v1/compare/backtests", params={"experiment_id": "one"})

    assert response.status_code == 422
