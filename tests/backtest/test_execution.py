"""Tests for executable rebalance fills."""

import pytest

from marketlab.backtest.accounting import Account
from marketlab.backtest.costs import simulate_fill
from marketlab.backtest.execution import rebalance_account
from marketlab.backtest.order import ExecutionQuote


def test_fill_applies_spread_impact_and_commission() -> None:
    quote = ExecutionQuote("2024-02-01", 10.0, 1_000_000.0)

    fill = simulate_fill("AAA", 1000, quote)

    assert fill is not None
    assert fill.execution_price > quote.open_price
    assert fill.total_cost > fill.commission


def test_rebalance_sells_before_cash_constrained_buys() -> None:
    account = Account(cash=0, holdings={"OLD": 100})
    quotes = {
        "OLD": ExecutionQuote("2024-02-01", 10.0, 1_000_000.0),
        "NEW": ExecutionQuote("2024-02-01", 10.0, 1_000_000.0),
    }

    fills, nav = rebalance_account(account, {"NEW": 1.0}, quotes)

    assert nav == 1000
    assert fills[0].quantity == -100
    assert account.holdings.get("OLD") is None
    assert account.cash >= 0
    assert account.holdings["NEW"] > 0


def test_capacity_caps_fill_quantity() -> None:
    quote = ExecutionQuote("2024-02-01", 10.0, 10_000.0)

    fill = simulate_fill("AAA", 1000, quote)

    assert fill is not None
    assert fill.quantity == 100
    assert fill.notional == pytest.approx(1000)


def test_fill_rejects_nonpositive_liquidity() -> None:
    quote = ExecutionQuote("2024-02-01", 10.0, 0.0)

    with pytest.raises(ValueError, match="positive"):
        simulate_fill("AAA", 100, quote)


def test_buy_quantity_is_reduced_for_exact_costs() -> None:
    account = Account(cash=1_000)
    quote = ExecutionQuote("2024-02-01", 10.0, 10_000.0)

    fills, _ = rebalance_account(account, {"AAA": 1.0}, {"AAA": quote})

    assert fills
    assert account.cash >= 0


def test_rebalance_applies_split_multiplier_before_valuation() -> None:
    account = Account(cash=0, holdings={"AAA": 100})
    quote = ExecutionQuote("2024-02-01", 5.0, 1_000_000.0, share_multiplier=2.0)

    _, nav = rebalance_account(account, {"AAA": 1.0}, {"AAA": quote})

    assert nav == 1_000
    assert account.holdings["AAA"] == 200
