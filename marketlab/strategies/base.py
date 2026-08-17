"""Common strategy interface."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class FactorSpec:
    """One ranked factor's contribution to a composite score."""

    name: str
    weight: float = 1.0
    higher_is_better: bool = True


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    """Long-only ranked portfolio construction settings."""

    name: str
    factors: tuple[FactorSpec, ...]
    selection_fraction: float = 0.2
    weighting: str = "equal"
    maximum_position: float = 0.05
    maximum_turnover: float = 0.20
    rebalance_frequency: Literal["weekly", "monthly"] = "monthly"
    signal_delay_sessions: int = 1

    def __post_init__(self) -> None:
        if not self.factors:
            raise ValueError("strategy requires at least one factor")
        if not 0 < self.selection_fraction <= 1:
            raise ValueError("selection_fraction must be in (0, 1]")
        if self.weighting not in {"equal", "score"}:
            raise ValueError("unsupported weighting method")
        if not 0 < self.maximum_position <= 1:
            raise ValueError("maximum_position must be in (0, 1]")
        if not 0 <= self.maximum_turnover <= 1:
            raise ValueError("maximum_turnover must be in [0, 1]")
        if self.signal_delay_sessions < 1:
            raise ValueError("signals must execute at least one session later")


def composite_score(row: dict[str, str], config: StrategyConfig) -> float | None:
    """Combine complete percentile ranks with explicit factor directions."""

    total_weight = sum(spec.weight for spec in config.factors)
    if total_weight <= 0:
        raise ValueError("factor weights must sum to a positive value")
    score = 0.0
    for spec in config.factors:
        value = row.get(f"{spec.name}_rank", "")
        if not value:
            return None
        rank = float(value)
        score += spec.weight * (rank if spec.higher_is_better else 1 - rank)
    return score / total_weight
