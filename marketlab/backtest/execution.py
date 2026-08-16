"""Target-weight order generation and execution simulation."""

import math

from marketlab.backtest.accounting import Account
from marketlab.backtest.costs import simulate_fill
from marketlab.backtest.order import ExecutionQuote, Fill

MINIMUM_TRADE_NOTIONAL = 1_000.0
MINIMUM_TARGET_WEIGHT = 0.0001


def rebalance_account(
    account: Account,
    target_weights: dict[str, float],
    quotes: dict[str, ExecutionQuote],
) -> tuple[list[Fill], float]:
    """Execute sells then cash-constrained buys toward target weights."""

    for symbol in list(account.holdings):
        quote = quotes.get(symbol)
        if quote is not None and quote.share_multiplier != 1:
            account.holdings[symbol] = round(
                account.holdings[symbol] * quote.share_multiplier
            )
    prices = {symbol: quote.open_price for symbol, quote in quotes.items()}
    net_asset_value = account.market_value(prices)
    if net_asset_value <= 0:
        raise ValueError("account net asset value must be positive")
    symbols = account.holdings.keys() | target_weights.keys()
    requested: dict[str, int] = {}
    for symbol in symbols:
        quote = quotes.get(symbol)
        if quote is None:
            continue
        target_weight = target_weights.get(symbol, 0)
        if target_weight < MINIMUM_TARGET_WEIGHT:
            target_weight = 0
        desired_shares = math.floor(target_weight * net_asset_value / quote.open_price)
        difference = desired_shares - account.holdings.get(symbol, 0)
        if (
            difference and abs(difference) * quote.open_price >= MINIMUM_TRADE_NOTIONAL
        ) or (target_weight == 0 and account.holdings.get(symbol, 0)):
            requested[symbol] = difference

    fills: list[Fill] = []
    for symbol in sorted(requested, key=lambda item: requested[item]):
        quantity = requested[symbol]
        if quantity >= 0:
            continue
        fill = simulate_fill(symbol, quantity, quotes[symbol])
        if fill is not None:
            account.apply(fill)
            fills.append(fill)
    for symbol in sorted(requested):
        quantity = requested[symbol]
        if quantity <= 0:
            continue
        quote = quotes[symbol]
        affordable = math.floor(
            max(0.0, account.cash - 1.0) / (quote.open_price * 1.0015)
        )
        fill = simulate_fill(symbol, min(quantity, affordable), quote)
        while fill is not None:
            cash_required = fill.quantity * fill.execution_price + fill.commission
            if cash_required <= account.cash + 1e-9:
                break
            reduced = math.floor(fill.quantity * account.cash / cash_required) - 1
            fill = simulate_fill(symbol, max(0, reduced), quote)
        if fill is not None:
            account.apply(fill)
            fills.append(fill)
    return fills, net_asset_value
