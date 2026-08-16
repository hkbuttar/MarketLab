"""Tests for out-of-sample ML portfolio evaluation."""

import pytest

from marketlab.ml.evaluation import _monthly_observation


def test_monthly_evaluation_builds_top_quintile_and_applies_turnover_cost() -> None:
    rows = [
        {
            "symbol": f"S{index}",
            "predicted_rank": str(index / 10),
            "target_return_rank": str(index / 10),
            "forward_return_21": str(index / 100),
        }
        for index in range(10)
    ]
    holdings = {}

    result = _monthly_observation(
        ("model", "2024-01-31"),
        rows,
        holdings,
        {"2024-01-31": 0.01},
        {"2024-01-31": 0.001},
        10.0,
    )

    assert result["rank_ic"] == pytest.approx(1.0)
    assert result["top_quintile_return"] == pytest.approx(0.085)
    assert result["bottom_quintile_return"] == pytest.approx(0.005)
    assert result["quantile_spread"] == pytest.approx(0.08)
    assert result["turnover"] == pytest.approx(0.5)
    assert result["transaction_cost"] == pytest.approx(0.0005)
    assert result["net_return"] == pytest.approx(0.0845)
