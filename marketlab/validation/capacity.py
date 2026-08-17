"""Liquidity-aware strategy capacity analysis."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityCapacity:
    """The capacity contribution of one security at a rebalance."""

    symbol: str
    weight_change: float
    average_dollar_volume: float
    maximum_aum: float


@dataclass(frozen=True)
class CapacityEstimate:
    """Portfolio capacity and its most restrictive trades."""

    maximum_aum: float
    maximum_adv_participation: float
    liquidation_days: int
    binding_securities: tuple[SecurityCapacity, ...]


@dataclass(frozen=True)
class CapacityPoint:
    """Trading-cost estimate at one strategy AUM level."""

    aum: float
    maximum_participation: float
    estimated_cost: float
    estimated_cost_bps: float
    feasible: bool


def estimate_capacity(
    weight_changes: dict[str, float],
    average_dollar_volume: dict[str, float],
    *,
    maximum_adv_participation: float = 0.10,
    liquidation_days: int = 1,
    binding_count: int = 5,
) -> CapacityEstimate:
    """Estimate AUM whose rebalance trades fit within an ADV participation cap."""

    _validate_assumptions(
        maximum_adv_participation, liquidation_days, binding_count=binding_count
    )
    active = {
        symbol: abs(change) for symbol, change in weight_changes.items() if change
    }
    if not active:
        raise ValueError("capacity requires at least one non-zero weight change")
    missing = active.keys() - average_dollar_volume.keys()
    if missing:
        raise ValueError(f"dollar volume is missing symbols: {sorted(missing)}")

    securities = []
    for symbol, change in active.items():
        if not math.isfinite(change):
            raise ValueError("weight changes must be finite")
        dollar_volume = average_dollar_volume[symbol]
        if not math.isfinite(dollar_volume) or dollar_volume <= 0:
            raise ValueError("average dollar volume must be finite and positive")
        maximum_aum = (
            dollar_volume * maximum_adv_participation * liquidation_days / change
        )
        securities.append(
            SecurityCapacity(
                symbol=symbol,
                weight_change=change,
                average_dollar_volume=dollar_volume,
                maximum_aum=maximum_aum,
            )
        )
    securities.sort(key=lambda item: (item.maximum_aum, item.symbol))
    return CapacityEstimate(
        maximum_aum=securities[0].maximum_aum,
        maximum_adv_participation=maximum_adv_participation,
        liquidation_days=liquidation_days,
        binding_securities=tuple(securities[:binding_count]),
    )


def capacity_curve(
    weight_changes: dict[str, float],
    average_dollar_volume: dict[str, float],
    aum_levels: list[float] | tuple[float, ...],
    *,
    maximum_adv_participation: float = 0.10,
    liquidation_days: int = 1,
    half_spread_fraction: float = 0.0005,
    impact_coefficient: float = 0.001,
) -> tuple[CapacityPoint, ...]:
    """Estimate spread and square-root impact costs across strategy AUM levels."""

    _validate_assumptions(maximum_adv_participation, liquidation_days)
    if half_spread_fraction < 0 or impact_coefficient < 0:
        raise ValueError("cost assumptions cannot be negative")
    active = {
        symbol: abs(change) for symbol, change in weight_changes.items() if change
    }
    missing = active.keys() - average_dollar_volume.keys()
    if missing:
        raise ValueError(f"dollar volume is missing symbols: {sorted(missing)}")
    if not active:
        raise ValueError("capacity requires at least one non-zero weight change")

    points = []
    for aum in aum_levels:
        if not math.isfinite(aum) or aum <= 0:
            raise ValueError("AUM levels must be finite and positive")
        total_cost = 0.0
        maximum_participation = 0.0
        for symbol, change in active.items():
            if not math.isfinite(change):
                raise ValueError("weight changes must be finite")
            dollar_volume = average_dollar_volume[symbol]
            if not math.isfinite(dollar_volume) or dollar_volume <= 0:
                raise ValueError("average dollar volume must be finite and positive")
            trade_notional = aum * change
            participation = trade_notional / (dollar_volume * liquidation_days)
            maximum_participation = max(maximum_participation, participation)
            total_cost += trade_notional * (
                half_spread_fraction + impact_coefficient * math.sqrt(participation)
            )
        points.append(
            CapacityPoint(
                aum=aum,
                maximum_participation=maximum_participation,
                estimated_cost=total_cost,
                estimated_cost_bps=total_cost / aum * 10_000,
                feasible=maximum_participation <= maximum_adv_participation + 1e-12,
            )
        )
    return tuple(points)


def _validate_assumptions(
    maximum_adv_participation: float,
    liquidation_days: int,
    *,
    binding_count: int = 1,
) -> None:
    if not 0 < maximum_adv_participation <= 1:
        raise ValueError("maximum_adv_participation must be in (0, 1]")
    if liquidation_days < 1:
        raise ValueError("liquidation_days must be positive")
    if binding_count < 1:
        raise ValueError("binding_count must be positive")
