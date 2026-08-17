"""Long-only short-horizon cross-sectional mean-reversion strategy."""

from marketlab.strategies.base import FactorSpec, StrategyConfig

MEAN_REVERSION = StrategyConfig(
    name="mean_reversion",
    factors=(FactorSpec("return_20d_zscore", higher_is_better=False),),
    selection_fraction=0.20,
    weighting="equal",
    maximum_position=0.05,
    maximum_turnover=0.50,
    rebalance_frequency="weekly",
    signal_delay_sessions=1,
)
