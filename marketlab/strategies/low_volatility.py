"""Low-volatility strategy."""

from marketlab.strategies.base import FactorSpec, StrategyConfig

LOW_VOLATILITY = StrategyConfig(
    name="low_volatility",
    factors=(FactorSpec("volatility_63", higher_is_better=False),),
)
