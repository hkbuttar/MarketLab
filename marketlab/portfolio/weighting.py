"""Target-weight construction."""

from marketlab.portfolio.constraints import apply_position_cap


def construct_weights(
    scores: dict[str, float],
    *,
    method: str,
    maximum_weight: float,
    risks: dict[str, float] | None = None,
) -> dict[str, float]:
    """Create capped equal, score, or inverse-volatility long-only weights."""

    if method == "equal":
        raw = {symbol: 1.0 for symbol in scores}
    elif method == "score":
        floor = min(scores.values(), default=0)
        raw = {symbol: score - floor + 1e-12 for symbol, score in scores.items()}
    elif method == "inverse_volatility":
        if risks is None:
            raise ValueError("inverse_volatility weighting requires risks")
        missing = scores.keys() - risks.keys()
        if missing:
            raise ValueError(f"risks are missing selected symbols: {sorted(missing)}")
        invalid = [symbol for symbol in scores if risks[symbol] <= 0]
        if invalid:
            raise ValueError(f"risks must be positive: {sorted(invalid)}")
        raw = {symbol: 1.0 / risks[symbol] for symbol in scores}
    else:
        raise ValueError("method must be 'equal', 'score', or 'inverse_volatility'")
    return apply_position_cap(raw, maximum_weight)
