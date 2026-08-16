"""Cash, position, and P&L accounting."""

from dataclasses import dataclass, field

from marketlab.backtest.order import Fill


@dataclass(slots=True)
class Account:
    """Cash and whole-share holdings for one simulated strategy."""

    cash: float
    holdings: dict[str, int] = field(default_factory=dict)

    def market_value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(
            quantity * prices[symbol]
            for symbol, quantity in self.holdings.items()
            if symbol in prices
        )

    def apply(self, fill: Fill) -> None:
        cash_change = -fill.quantity * fill.execution_price - fill.commission
        if cash_change < 0 and -cash_change > self.cash + 1e-9:
            raise ValueError("fill would overdraw account cash")
        self.cash += cash_change
        quantity = self.holdings.get(fill.symbol, 0) + fill.quantity
        if quantity:
            self.holdings[fill.symbol] = quantity
        else:
            self.holdings.pop(fill.symbol, None)
