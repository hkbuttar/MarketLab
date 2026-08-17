"""Portfolio constraints."""


def limit_holdings(scores: dict[str, float], maximum_holdings: int) -> dict[str, float]:
    """Keep the highest scores with deterministic symbol tie-breaking."""

    if maximum_holdings < 1:
        raise ValueError("maximum_holdings must be positive")
    return dict(
        sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:maximum_holdings]
    )


def filter_minimum_liquidity(
    scores: dict[str, float],
    dollar_volume: dict[str, float],
    minimum_dollar_volume: float,
) -> dict[str, float]:
    """Exclude missing or insufficient point-in-time liquidity observations."""

    if minimum_dollar_volume < 0:
        raise ValueError("minimum_dollar_volume cannot be negative")
    return {
        symbol: score
        for symbol, score in scores.items()
        if dollar_volume.get(symbol, -1) >= minimum_dollar_volume
    }


def apply_cash_buffer(
    risky_weights: dict[str, float], cash_buffer: float
) -> dict[str, float]:
    """Scale risky weights so a fixed fraction of NAV remains in cash."""

    if not 0 <= cash_buffer < 1:
        raise ValueError("cash_buffer must be in [0, 1)")
    total = sum(risky_weights.values())
    if not risky_weights:
        return {}
    if not abs(total - 1.0) <= 1e-9:
        raise ValueError("risky weights must sum to one before applying cash buffer")
    return {
        symbol: weight * (1.0 - cash_buffer) for symbol, weight in risky_weights.items()
    }


def apply_sector_cap(
    raw_weights: dict[str, float],
    sectors: dict[str, str],
    maximum_sector_weight: float,
) -> dict[str, float]:
    """Cap sectors and redistribute excess proportionally across other sectors."""

    if not 0 < maximum_sector_weight <= 1:
        raise ValueError("maximum_sector_weight must be in (0, 1]")
    positive = {symbol: weight for symbol, weight in raw_weights.items() if weight > 0}
    missing = positive.keys() - sectors.keys()
    if missing:
        raise ValueError(f"sectors are missing symbols: {sorted(missing)}")
    if not positive:
        return {}
    total = sum(positive.values())
    names = {sectors[symbol] for symbol in positive}
    if len(names) * maximum_sector_weight < total - 1e-12:
        raise ValueError("sector cap is infeasible for the represented sectors")
    remaining = dict(positive)
    fixed: dict[str, float] = {}
    while remaining:
        available = total - sum(fixed.values())
        remaining_total = sum(remaining.values())
        projected = {
            sector: sum(
                weight * available / remaining_total
                for symbol, weight in remaining.items()
                if sectors[symbol] == sector
            )
            for sector in {sectors[symbol] for symbol in remaining}
        }
        breaches = {
            sector
            for sector, weight in projected.items()
            if weight > maximum_sector_weight + 1e-12
        }
        if not breaches:
            fixed.update(
                {
                    symbol: weight * available / remaining_total
                    for symbol, weight in remaining.items()
                }
            )
            break
        for sector in breaches:
            members = {
                symbol: weight
                for symbol, weight in remaining.items()
                if sectors[symbol] == sector
            }
            sector_total = sum(members.values())
            fixed.update(
                {
                    symbol: weight / sector_total * maximum_sector_weight
                    for symbol, weight in members.items()
                }
            )
            for symbol in members:
                remaining.pop(symbol)
    return fixed


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
