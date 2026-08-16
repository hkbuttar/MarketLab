"""Target-weight construction."""

from marketlab.portfolio.constraints import apply_position_cap


def construct_weights(
    scores: dict[str, float], *, method: str, maximum_weight: float
) -> dict[str, float]:
    """Create capped equal or score-proportional long-only weights."""

    if method == "equal":
        raw = {symbol: 1.0 for symbol in scores}
    elif method == "score":
        floor = min(scores.values(), default=0)
        raw = {symbol: score - floor + 1e-12 for symbol, score in scores.items()}
    else:
        raise ValueError("method must be 'equal' or 'score'")
    return apply_position_cap(raw, maximum_weight)
