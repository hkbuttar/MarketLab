"""Tests for constrained portfolio construction helpers."""

import pytest

from marketlab.portfolio.constraints import apply_position_cap
from marketlab.portfolio.turnover import limit_turnover, one_way_turnover
from marketlab.strategies.base import FactorSpec, StrategyConfig, composite_score


def test_position_cap_redistributes_excess_weight() -> None:
    weights = apply_position_cap({"A": 9, "B": 1, "C": 1}, 0.5)

    assert sum(weights.values()) == pytest.approx(1)
    assert weights["A"] == 0.5
    assert max(weights.values()) <= 0.5


def test_infeasible_position_cap_is_rejected() -> None:
    with pytest.raises(ValueError, match="infeasible"):
        apply_position_cap({"A": 1, "B": 1}, 0.4)


def test_turnover_blending_respects_limit() -> None:
    current = {"A": 0.5, "B": 0.5}
    target = {"C": 0.5, "D": 0.5}

    weights, turnover = limit_turnover(current, target, 0.2)

    assert turnover == pytest.approx(0.2)
    assert one_way_turnover(current, weights) == pytest.approx(0.2)
    assert sum(weights.values()) == pytest.approx(1)


def test_composite_score_applies_factor_direction() -> None:
    config = StrategyConfig(
        name="test",
        factors=(FactorSpec("quality"), FactorSpec("risk", higher_is_better=False)),
    )

    score = composite_score({"quality_rank": "0.8", "risk_rank": "0.2"}, config)

    assert score == pytest.approx(0.8)
