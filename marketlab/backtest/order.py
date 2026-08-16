"""Order and fill domain models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionQuote:
    """Next-session execution inputs known after a rebalance signal."""

    execution_date: str
    open_price: float
    average_dollar_volume: float
    share_multiplier: float = 1.0


@dataclass(frozen=True, slots=True)
class Fill:
    """One simulated whole-share execution."""

    symbol: str
    quantity: int
    reference_price: float
    execution_price: float
    commission: float
    spread_cost: float
    impact_cost: float

    @property
    def notional(self) -> float:
        return abs(self.quantity) * self.reference_price

    @property
    def total_cost(self) -> float:
        return self.commission + self.spread_cost + self.impact_cost
