"""Benchmark-relative analytics."""

import math

from marketlab.analytics.returns import TRADING_DAYS, _sample_std


def benchmark_statistics(
    returns: list[float], benchmark_returns: list[float]
) -> dict[str, float]:
    """Calculate OLS alpha/beta and active-return statistics."""

    if len(returns) != len(benchmark_returns):
        raise ValueError("strategy and benchmark returns must be aligned")
    if len(returns) < 2:
        return {
            key: 0.0
            for key in (
                "alpha",
                "beta",
                "tracking_error",
                "information_ratio",
                "correlation",
            )
        }
    mean = sum(returns) / len(returns)
    benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)
    covariance = sum(
        (value - mean) * (reference - benchmark_mean)
        for value, reference in zip(returns, benchmark_returns, strict=True)
    ) / (len(returns) - 1)
    benchmark_variance = _sample_std(benchmark_returns) ** 2
    beta = covariance / benchmark_variance if benchmark_variance else 0.0
    alpha = (mean - beta * benchmark_mean) * TRADING_DAYS
    active = [
        value - reference
        for value, reference in zip(returns, benchmark_returns, strict=True)
    ]
    tracking_error = _sample_std(active) * math.sqrt(TRADING_DAYS)
    information_ratio = (
        (sum(active) / len(active) * TRADING_DAYS / tracking_error)
        if tracking_error
        else 0.0
    )
    denominator = _sample_std(returns) * _sample_std(benchmark_returns)
    correlation = covariance / denominator if denominator else 0.0
    return {
        "alpha": alpha,
        "beta": beta,
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
        "correlation": correlation,
    }
