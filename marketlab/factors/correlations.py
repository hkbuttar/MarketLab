"""Factor correlation and redundancy analysis."""

import math


def pearson_correlation(
    first: list[float | None], second: list[float | None]
) -> float | None:
    """Return Pearson correlation for finite complete pairs."""

    pairs = [
        (left, right)
        for left, right in zip(first, second, strict=True)
        if left is not None
        and right is not None
        and math.isfinite(left)
        and math.isfinite(right)
    ]
    if len(pairs) < 3:
        return None
    left_mean = sum(left for left, _ in pairs) / len(pairs)
    right_mean = sum(right for _, right in pairs) / len(pairs)
    numerator = sum((left - left_mean) * (right - right_mean) for left, right in pairs)
    left_scale = sum((left - left_mean) ** 2 for left, _ in pairs)
    right_scale = sum((right - right_mean) ** 2 for _, right in pairs)
    denominator = math.sqrt(left_scale * right_scale)
    return numerator / denominator if denominator else None
