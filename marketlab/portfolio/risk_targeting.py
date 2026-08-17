"""Transparent portfolio-level volatility targeting."""

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskTargetResult:
    """Risky weights, residual cash, and achieved exposure diagnostics."""

    weights: dict[str, float]
    cash_weight: float
    scale: float
    gross_exposure: float
    estimated_volatility: float


def portfolio_volatility(
    weights: dict[str, float], covariance: dict[str, dict[str, float]]
) -> float:
    """Calculate annualized portfolio volatility from an annual covariance matrix."""

    if any(weight < 0 for weight in weights.values()):
        raise ValueError("risk targeting supports long-only weights")
    variance = 0.0
    for left, left_weight in weights.items():
        if left not in covariance:
            raise ValueError(f"covariance is missing symbol: {left}")
        for right, right_weight in weights.items():
            if right not in covariance[left]:
                raise ValueError(f"covariance is missing pair: {left}, {right}")
            variance += left_weight * right_weight * covariance[left][right]
    if variance < -1e-12:
        raise ValueError("covariance produces negative portfolio variance")
    return math.sqrt(max(variance, 0.0))


def target_volatility(
    weights: dict[str, float],
    observed_volatility: float,
    target: float,
    *,
    allow_leverage: bool = False,
    maximum_leverage: float = 1.0,
    maximum_position: float | None = None,
) -> RiskTargetResult:
    """Scale risky exposure toward a target, leaving the remainder in cash."""

    if not weights or any(weight < 0 for weight in weights.values()):
        raise ValueError("weights must be a non-empty long-only portfolio")
    if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("input risky weights must sum to one")
    if observed_volatility <= 0 or target <= 0:
        raise ValueError("observed and target volatility must be positive")
    if maximum_leverage < 1:
        raise ValueError("maximum_leverage must be at least one")
    if maximum_position is not None and not 0 < maximum_position <= 1:
        raise ValueError("maximum_position must be in (0, 1]")
    exposure_limit = maximum_leverage if allow_leverage else 1.0
    if maximum_position is not None:
        exposure_limit = min(exposure_limit, maximum_position / max(weights.values()))
    scale = min(target / observed_volatility, exposure_limit)
    scaled = {symbol: weight * scale for symbol, weight in weights.items()}
    gross = sum(scaled.values())
    return RiskTargetResult(
        weights=scaled,
        cash_weight=max(0.0, 1.0 - gross),
        scale=scale,
        gross_exposure=gross,
        estimated_volatility=observed_volatility * scale,
    )
