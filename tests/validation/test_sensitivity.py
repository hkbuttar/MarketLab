"""Tests for neighboring-parameter sensitivity analysis."""

import pytest

from marketlab.validation.sensitivity import (
    MOMENTUM_WINDOWS,
    VOLATILITY_WINDOWS,
    _evaluate_cross_section,
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
