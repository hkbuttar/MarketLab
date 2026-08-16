"""Factor quantile portfolio analysis."""

from collections import defaultdict


def quantile_mean_returns(
    quantiles: list[int | None], forward_returns: list[float | None]
) -> dict[int, float]:
    """Return equal-weight mean forward returns for populated quantiles."""

    groups: dict[int, list[float]] = defaultdict(list)
    for bucket, forward in zip(quantiles, forward_returns, strict=True):
        if bucket is not None and forward is not None:
            groups[bucket].append(forward)
    return {bucket: sum(values) / len(values) for bucket, values in groups.items()}
