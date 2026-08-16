"""Tests for performance and risk analytics."""

import csv
import gzip
import math

import pytest

from marketlab.analytics.benchmark import benchmark_statistics
from marketlab.analytics.drawdown import drawdown_statistics
from marketlab.analytics.returns import (
    annualized_return,
    compounded_return,
    period_returns,
    sharpe_ratio,
)
from marketlab.analytics.risk import historical_cvar, historical_var
from marketlab.analytics.turnover import portfolio_statistics


def test_compounded_and_annualized_returns() -> None:
    returns = [0.10, -0.10]

    assert compounded_return(returns) == pytest.approx(-0.01)
    assert annualized_return([0.01] * 252) == pytest.approx(1.01**252 - 1)


def test_period_returns_compound_by_calendar_period() -> None:
    result = period_returns(
        ["2024-01-30", "2024-01-31", "2024-02-01"], [0.10, -0.10, 0.05]
    )

    assert result["monthly"]["2024-01"] == pytest.approx(-0.01)
    assert result["monthly"]["2024-02"] == pytest.approx(0.05)
    assert result["annual"]["2024"] == pytest.approx(0.0395)


def test_drawdown_tracks_peak_trough_and_recovery() -> None:
    result = drawdown_statistics(
        [100.0, 120.0, 90.0, 121.0],
        ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
    )

    assert result["maximum_drawdown"] == pytest.approx(-0.25)
    assert result["peak_date"] == "2024-01-02"
    assert result["trough_date"] == "2024-01-03"
    assert result["recovery_date"] == "2024-01-04"
    assert result["duration_days"] == 2


def test_historical_tail_risk_uses_worst_observations() -> None:
    returns = [-0.10, -0.05] + [0.01] * 38

    assert historical_var(returns) == pytest.approx(0.05)
    assert historical_cvar(returns) == pytest.approx(0.075)


def test_benchmark_statistics_for_double_benchmark_returns() -> None:
    benchmark = [-0.01, 0.0, 0.01, 0.02]
    strategy = [2 * value for value in benchmark]
    result = benchmark_statistics(strategy, benchmark)

    assert result["beta"] == pytest.approx(2.0)
    assert result["alpha"] == pytest.approx(0.0)
    assert result["correlation"] == pytest.approx(1.0)


def test_sharpe_is_finite_for_varying_returns() -> None:
    assert math.isfinite(sharpe_ratio([0.01, -0.005, 0.002]))


def test_portfolio_statistics_aggregate_each_rebalance_once(tmp_path) -> None:
    path = tmp_path / "targets.csv.gz"
    with gzip.open(path, "wt", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=("strategy", "date", "symbol", "turnover")
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "strategy": "value",
                    "date": "2024-01-31",
                    "symbol": "A",
                    "turnover": 0.5,
                },
                {
                    "strategy": "value",
                    "date": "2024-01-31",
                    "symbol": "B",
                    "turnover": 0.5,
                },
                {
                    "strategy": "value",
                    "date": "2024-02-29",
                    "symbol": "A",
                    "turnover": 0.2,
                },
            ]
        )

    result = portfolio_statistics(path)["value"]

    assert result["average_holdings"] == pytest.approx(1.5)
    assert result["average_monthly_turnover"] == pytest.approx(0.35)
    assert result["annualized_turnover"] == pytest.approx(4.2)
