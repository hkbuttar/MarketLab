"""Tests for neighboring-parameter sensitivity analysis."""

import csv
import gzip

import pytest

from marketlab.validation.sensitivity import (
    MOMENTUM_WINDOWS,
    VOLATILITY_WINDOWS,
    _evaluate_cross_section,
    run_cost_sensitivity,
)


def test_cross_section_selects_high_momentum_and_low_volatility() -> None:
    rows = []
    for index in range(10):
        row = {
            "forward_return_21": str(index / 100),
            **{f"momentum_{window}": str(index) for window in MOMENTUM_WINDOWS},
            **{f"volatility_{window}": str(index) for window in VOLATILITY_WINDOWS},
        }
        rows.append(row)
    monthly = {}

    _evaluate_cross_section(rows, monthly)

    assert monthly[("momentum", 126, 0.10)] == [pytest.approx(0.0891)]
    assert monthly[("volatility", 20, 0.10)] == [pytest.approx(0.0009)]
    assert len(monthly) == 18


def test_cost_sensitivity_replays_gross_returns_and_traded_notional(tmp_path) -> None:
    results = tmp_path / "results.csv"
    with results.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "strategy", "gross_nav"))
        writer.writeheader()
        writer.writerows(
            [
                {"date": "2024-01-02", "strategy": "test", "gross_nav": 1_100_000},
                {"date": "2024-01-03", "strategy": "test", "gross_nav": 1_210_000},
            ]
        )
    trades = tmp_path / "trades.csv.gz"
    with gzip.open(trades, "wt", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=("strategy", "execution_date", "notional")
        )
        writer.writeheader()
        writer.writerow(
            {"strategy": "test", "execution_date": "2024-01-02", "notional": 100_000}
        )
    factors = tmp_path / "factors.csv.gz"
    with gzip.open(factors, "wt", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "risk_free"))
        writer.writeheader()
        writer.writerows(
            [
                {"date": "2024-01-02", "risk_free": 0.0},
                {"date": "2024-01-03", "risk_free": 0.0},
            ]
        )

    rows = run_cost_sensitivity(results, trades, factors, tmp_path / "output")

    zero = next(row for row in rows if row["cost_bps"] == 0)
    fifty = next(row for row in rows if row["cost_bps"] == 50)
    assert zero["ending_nav"] == pytest.approx(1_210_000)
    assert fifty["total_scenario_costs"] == pytest.approx(500)
    assert fifty["ending_nav"] == pytest.approx(1_209_450)
