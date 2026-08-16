"""Portfolio constraints."""


def apply_position_cap(
    raw_weights: dict[str, float], maximum_weight: float
) -> dict[str, float]:
    """Normalize long-only weights while redistributing weight above a cap."""

    if not 0 < maximum_weight <= 1:
        raise ValueError("maximum_weight must be in (0, 1]")
    positive = {symbol: value for symbol, value in raw_weights.items() if value > 0}
    if not positive:
        return {}
    if len(positive) * maximum_weight < 1 - 1e-12:
        raise ValueError("position cap is infeasible for the selected holdings")
    weights = {
        symbol: value / sum(positive.values()) for symbol, value in positive.items()
    }
    fixed: dict[str, float] = {}
    remaining = dict(weights)
    while remaining:
        available = 1 - sum(fixed.values())
        scale = available / sum(remaining.values())
        breaches = {
            symbol
            for symbol, value in remaining.items()
            if value * scale > maximum_weight
        }
        if not breaches:
            fixed.update({symbol: value * scale for symbol, value in remaining.items()})
            break
        for symbol in breaches:
            fixed[symbol] = maximum_weight
            remaining.pop(symbol)
    return fixed
