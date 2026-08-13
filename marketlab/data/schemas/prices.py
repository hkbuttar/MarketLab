"""Canonical daily adjusted-price record."""

from dataclasses import dataclass
from datetime import datetime

from marketlab.data.schemas._types import (
    Numeric,
    column_names,
    require_datetime,
    require_float,
    require_numeric,
    require_string,
)


@dataclass(frozen=True, slots=True)
class PriceRecord:
    """One daily OHLCV observation for a security."""

    date: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: Numeric

    def __post_init__(self) -> None:
        require_datetime(self.date, "date")
        require_string(self.symbol, "symbol")
        for field_name in ("open", "high", "low", "close", "adjusted_close"):
            require_float(getattr(self, field_name), field_name)
        require_numeric(self.volume, "volume")


PRICE_COLUMNS = column_names(PriceRecord)
PRICE_PRIMARY_KEY = ("date", "symbol")
