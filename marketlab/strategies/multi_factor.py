"""Multi-factor strategy."""

from marketlab.strategies.base import FactorSpec, StrategyConfig

QUALITY_VALUE_MOMENTUM = StrategyConfig(
    name="quality_value_momentum",
    factors=(
        FactorSpec("earnings_yield", 0.30),
        FactorSpec("gross_profitability", 0.30),
        FactorSpec("momentum_12_1", 0.20),
        FactorSpec("volatility_63", 0.20, higher_is_better=False),
    ),
    weighting="score",
)
