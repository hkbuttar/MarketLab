"""Portfolio risk metrics."""

import math

from marketlab.analytics.returns import TRADING_DAYS, _sample_std


def annualized_volatility(returns: list[float]) -> float:
    """Calculate sample volatility annualized from daily observations."""

    return _sample_std(returns) * math.sqrt(TRADING_DAYS)


def downside_deviation(returns: list[float]) -> float:
    """Calculate annualized zero-target downside deviation."""

    if not returns:
        return 0.0
    return math.sqrt(
        sum(min(value, 0.0) ** 2 for value in returns) / len(returns)
    ) * math.sqrt(TRADING_DAYS)


def historical_var(returns: list[float], confidence: float = 0.95) -> float:
    """Calculate historical one-day VaR as a positive loss fraction."""

    if not returns:
        return 0.0
    ordered = sorted(returns)
    index = max(0, math.ceil((1.0 - confidence) * len(ordered) - 1e-12) - 1)
    return max(0.0, -ordered[index])


def historical_cvar(returns: list[float], confidence: float = 0.95) -> float:
    """Calculate mean one-day loss at or beyond historical VaR."""

    if not returns:
        return 0.0
    ordered = sorted(returns)
    count = max(1, math.ceil((1.0 - confidence) * len(ordered) - 1e-12))
    return max(0.0, -sum(ordered[:count]) / count)
