"""Tests for constrained portfolio construction helpers."""

import pytest

from marketlab.portfolio.constraints import apply_position_cap
from marketlab.portfolio.risk_targeting import portfolio_volatility, target_volatility
from marketlab.portfolio.turnover import limit_turnover, one_way_turnover
from marketlab.portfolio.weighting import construct_weights
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


def test_inverse_volatility_weighting_allocates_more_to_lower_risk() -> None:
    weights = construct_weights(
        {"LOW": 1.0, "HIGH": 1.0},
        method="inverse_volatility",
        risks={"LOW": 0.10, "HIGH": 0.20},
        maximum_weight=0.80,
    )

    assert weights == pytest.approx({"LOW": 2 / 3, "HIGH": 1 / 3})


def test_inverse_volatility_rejects_zero_or_missing_risk() -> None:
    with pytest.raises(ValueError, match="positive"):
        construct_weights(
            {"A": 1},
            method="inverse_volatility",
            risks={"A": 0},
            maximum_weight=1,
        )
    with pytest.raises(ValueError, match="missing"):
        construct_weights(
            {"A": 1},
            method="inverse_volatility",
            risks={},
            maximum_weight=1,
        )


def test_risk_targeting_deleverages_into_cash() -> None:
    result = target_volatility({"A": 0.6, "B": 0.4}, 0.20, 0.10)

    assert result.weights == pytest.approx({"A": 0.3, "B": 0.2})
    assert result.cash_weight == pytest.approx(0.5)
    assert result.gross_exposure == pytest.approx(0.5)
    assert result.estimated_volatility == pytest.approx(0.10)


def test_risk_targeting_caps_leverage_and_positions() -> None:
    result = target_volatility(
        {"A": 0.6, "B": 0.4},
        0.08,
        0.12,
        allow_leverage=True,
        maximum_leverage=1.5,
        maximum_position=0.70,
    )

    assert result.scale == pytest.approx(0.70 / 0.60)
    assert result.weights["A"] == pytest.approx(0.70)
    assert result.cash_weight == 0
    assert result.gross_exposure == pytest.approx(7 / 6)


def test_portfolio_volatility_uses_covariance() -> None:
    value = portfolio_volatility(
        {"A": 0.5, "B": 0.5},
        {"A": {"A": 0.04, "B": 0.01}, "B": {"A": 0.01, "B": 0.09}},
    )

    assert value == pytest.approx((0.0375) ** 0.5)
