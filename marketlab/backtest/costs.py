"""Commission, spread, slippage, and impact models."""

import math

from marketlab.backtest.order import ExecutionQuote, Fill


def simulate_fill(
    symbol: str,
    requested_quantity: int,
    quote: ExecutionQuote,
    *,
    maximum_adv_participation: float = 0.10,
) -> Fill | None:
    """Apply capacity, whole-share, commission, spread, and impact costs."""

    if requested_quantity == 0:
        return None
    if quote.open_price <= 0 or quote.average_dollar_volume <= 0:
        raise ValueError("execution quote prices and liquidity must be positive")
    maximum_shares = math.floor(
        quote.average_dollar_volume * maximum_adv_participation / quote.open_price
    )
    quantity = max(-maximum_shares, min(maximum_shares, requested_quantity))
    if quantity == 0:
        return None
    notional = abs(quantity) * quote.open_price
    participation = notional / quote.average_dollar_volume
    half_spread_fraction = 0.0005
    impact_fraction = 0.001 * math.sqrt(participation)
    direction = 1 if quantity > 0 else -1
    execution_price = quote.open_price * (
        1 + direction * (half_spread_fraction + impact_fraction)
    )
    return Fill(
        symbol=symbol,
        quantity=quantity,
        reference_price=quote.open_price,
        execution_price=execution_price,
        commission=max(1.0, 0.005 * abs(quantity)),
        spread_cost=notional * half_spread_fraction,
        impact_cost=notional * impact_fraction,
    )
