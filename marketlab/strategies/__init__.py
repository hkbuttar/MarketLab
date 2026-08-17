"""Systematic strategy definitions and discovery."""

from marketlab.strategies.low_volatility import LOW_VOLATILITY
from marketlab.strategies.mean_reversion import MEAN_REVERSION
from marketlab.strategies.momentum import MOMENTUM
from marketlab.strategies.multi_factor import QUALITY_VALUE_MOMENTUM

STRATEGIES = {
    strategy.name: strategy
    for strategy in (
        MOMENTUM,
        MEAN_REVERSION,
        LOW_VOLATILITY,
        QUALITY_VALUE_MOMENTUM,
    )
}

__all__ = [
    "LOW_VOLATILITY",
    "MEAN_REVERSION",
    "MOMENTUM",
    "QUALITY_VALUE_MOMENTUM",
    "STRATEGIES",
]
