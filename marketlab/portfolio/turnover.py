"""Portfolio turnover controls."""


def one_way_turnover(current: dict[str, float], target: dict[str, float]) -> float:
    """Return half the absolute change across fully invested risky weights."""

    symbols = current.keys() | target.keys()
    return 0.5 * sum(
        abs(target.get(symbol, 0) - current.get(symbol, 0)) for symbol in symbols
    )


def limit_turnover(
    current: dict[str, float], target: dict[str, float], maximum_turnover: float
) -> tuple[dict[str, float], float]:
    """Blend toward target weights until the one-way turnover limit is met."""

    if not 0 <= maximum_turnover <= 1:
        raise ValueError("maximum_turnover must be in [0, 1]")
    required = one_way_turnover(current, target)
    if required <= maximum_turnover or not current:
        return target, required
    fraction = maximum_turnover / required
    symbols = current.keys() | target.keys()
    blended = {
        symbol: current.get(symbol, 0)
        + fraction * (target.get(symbol, 0) - current.get(symbol, 0))
        for symbol in symbols
    }
    return {
        symbol: weight for symbol, weight in blended.items() if weight > 1e-15
    }, maximum_turnover
