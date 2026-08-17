"""Tests for liquidity-aware capacity analysis."""

import math

import pytest

from marketlab.validation.capacity import capacity_curve, estimate_capacity


def test_capacity_is_set_by_most_restrictive_trade() -> None:
    result = estimate_capacity(
        {"LIQUID": 0.10, "BINDING": -0.05},
        {"LIQUID": 100_000_000, "BINDING": 10_000_000},
        maximum_adv_participation=0.10,
    )

    assert result.maximum_aum == pytest.approx(20_000_000)
    assert result.binding_securities[0].symbol == "BINDING"
    assert result.binding_securities[0].weight_change == pytest.approx(0.05)


def test_liquidation_window_increases_capacity() -> None:
    one_day = estimate_capacity({"A": 0.2}, {"A": 20_000_000})
    five_days = estimate_capacity({"A": 0.2}, {"A": 20_000_000}, liquidation_days=5)

    assert five_days.maximum_aum == pytest.approx(one_day.maximum_aum * 5)


def test_capacity_curve_reports_cost_and_feasibility() -> None:
    points = capacity_curve(
        {"A": 0.10, "B": -0.10},
        {"A": 10_000_000, "B": 20_000_000},
        [5_000_000, 20_000_000],
        maximum_adv_participation=0.10,
    )

    assert points[0].feasible is True
    assert points[1].feasible is False
    assert points[1].maximum_participation == pytest.approx(0.20)
    assert points[1].estimated_cost > points[0].estimated_cost
    assert points[1].estimated_cost_bps > points[0].estimated_cost_bps


def test_capacity_rejects_missing_or_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="missing"):
        estimate_capacity({"A": 0.1}, {})
    with pytest.raises(ValueError, match="positive"):
        estimate_capacity({"A": 0.1}, {"A": 0})
    with pytest.raises(ValueError, match="non-zero"):
        estimate_capacity({"A": 0}, {"A": 1_000_000})
    with pytest.raises(ValueError, match="finite"):
        estimate_capacity({"A": math.nan}, {"A": 1_000_000})
    with pytest.raises(ValueError, match="AUM"):
        capacity_curve({"A": 0.1}, {"A": 1_000_000}, [0])
