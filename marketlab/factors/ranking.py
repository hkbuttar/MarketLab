"""Cross-sectional factor ranking."""

import math


def percentile_ranks(values: list[float | None]) -> list[float | None]:
    """Return average-tie percentile ranks while preserving missing positions."""

    valid = sorted(
        (value, index)
        for index, value in enumerate(values)
        if value is not None and math.isfinite(value)
    )
    result: list[float | None] = [None] * len(values)
    if not valid:
        return result
    position = 0
    while position < len(valid):
        end = position + 1
        while end < len(valid) and valid[end][0] == valid[position][0]:
            end += 1
        average_rank = ((position + 1) + end) / 2
        percentile = average_rank / len(valid)
        for _, original_index in valid[position:end]:
            result[original_index] = percentile
        position = end
    return result


def quantile(rank: float | None, buckets: int = 5) -> int | None:
    """Map a percentile rank to an integer quantile from one to buckets."""

    if rank is None:
        return None
    return min(buckets, max(1, math.ceil(rank * buckets)))
