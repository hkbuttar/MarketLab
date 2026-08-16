"""Cross-sectional momentum strategy."""

from marketlab.strategies.base import FactorSpec, StrategyConfig

MOMENTUM = StrategyConfig(
    name="momentum",
    factors=(FactorSpec("momentum_12_1"),),
)
