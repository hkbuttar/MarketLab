"""Return and risk-adjusted performance metrics."""

import math
from collections import defaultdict

TRADING_DAYS = 252


def compounded_return(returns: list[float]) -> float:
    """Return the geometrically compounded return."""

    wealth = 1.0
    for value in returns:
        wealth *= 1.0 + value
    return wealth - 1.0


def annualized_return(returns: list[float], periods: int = TRADING_DAYS) -> float:
    """Annualize a daily return series geometrically."""

    if not returns:
        return 0.0
    wealth = 1.0 + compounded_return(returns)
    return wealth ** (periods / len(returns)) - 1.0 if wealth > 0 else -1.0


def sharpe_ratio(
    returns: list[float], risk_free_rate: float = 0.0, periods: int = TRADING_DAYS
) -> float:
    """Calculate annualized Sharpe using a constant annual risk-free rate."""

    if len(returns) < 2:
        return 0.0
    daily_risk_free = (1.0 + risk_free_rate) ** (1.0 / periods) - 1.0
    excess = [value - daily_risk_free for value in returns]
    volatility = _sample_std(excess)
    return (
        math.sqrt(periods) * sum(excess) / len(excess) / volatility
        if volatility
        else 0.0
    )


def sortino_ratio(
    returns: list[float], risk_free_rate: float = 0.0, periods: int = TRADING_DAYS
) -> float:
    """Calculate annualized Sortino using zero-clipped downside deviation."""

    if not returns:
        return 0.0
    daily_risk_free = (1.0 + risk_free_rate) ** (1.0 / periods) - 1.0
    excess = [value - daily_risk_free for value in returns]
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in excess) / len(excess))
    return (
        math.sqrt(periods) * sum(excess) / len(excess) / downside if downside else 0.0
    )


def period_returns(
    dates: list[str], returns: list[float]
) -> dict[str, dict[str, float]]:
    """Compound daily observations into calendar-month and calendar-year returns."""

    monthly: dict[str, list[float]] = defaultdict(list)
    annual: dict[str, list[float]] = defaultdict(list)
    for date, value in zip(dates, returns, strict=True):
        monthly[date[:7]].append(value)
        annual[date[:4]].append(value)
    return {
        "monthly": {key: compounded_return(values) for key, values in monthly.items()},
        "annual": {key: compounded_return(values) for key, values in annual.items()},
    }


def _sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
