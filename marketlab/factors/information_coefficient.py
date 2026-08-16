"""Factor information-coefficient analysis."""

import math

from marketlab.factors.ranking import percentile_ranks


def spearman_ic(
    values: list[float | None], forward_returns: list[float | None]
) -> float | None:
    """Calculate cross-sectional Spearman correlation on complete pairs."""

    pairs = [
        (value, forward)
        for value, forward in zip(values, forward_returns, strict=True)
        if value is not None
        and forward is not None
        and math.isfinite(value)
        and math.isfinite(forward)
    ]
    if len(pairs) < 3:
        return None
    x_ranks = percentile_ranks([pair[0] for pair in pairs])
    y_ranks = percentile_ranks([pair[1] for pair in pairs])
    return _correlation(
        [value for value in x_ranks if value is not None],
        [value for value in y_ranks if value is not None],
    )


def _correlation(x: list[float], y: list[float]) -> float | None:
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y, strict=True))
    x_scale = sum((value - x_mean) ** 2 for value in x)
    y_scale = sum((value - y_mean) ** 2 for value in y)
    denominator = math.sqrt(x_scale * y_scale)
    return numerator / denominator if denominator else None
