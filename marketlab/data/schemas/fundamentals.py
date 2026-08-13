"""Canonical point-in-time fundamental-data record."""

from dataclasses import dataclass
from datetime import datetime

from marketlab.data.schemas._types import (
    Numeric,
    column_names,
    require_datetime,
    require_numeric,
    require_string,
)


@dataclass(frozen=True, slots=True)
class FundamentalRecord:
    """One reported fiscal period with its historical availability date."""

    symbol: str
    fiscal_period: str
    report_date: datetime
    available_date: datetime
    market_cap: Numeric | None
    book_value: Numeric | None
    net_income: Numeric | None
    revenue: Numeric | None
    gross_profit: Numeric | None
    assets: Numeric | None
    debt: Numeric | None
    free_cash_flow: Numeric | None
    shares_outstanding: Numeric | None

    def __post_init__(self) -> None:
        require_string(self.symbol, "symbol")
        require_string(self.fiscal_period, "fiscal_period")
        require_datetime(self.report_date, "report_date")
        require_datetime(self.available_date, "available_date")
        for field_name in FUNDAMENTAL_NUMERIC_COLUMNS:
            require_numeric(getattr(self, field_name), field_name, optional=True)


FUNDAMENTAL_NUMERIC_COLUMNS = (
    "market_cap",
    "book_value",
    "net_income",
    "revenue",
    "gross_profit",
    "assets",
    "debt",
    "free_cash_flow",
    "shares_outstanding",
)
FUNDAMENTAL_COLUMNS = column_names(FundamentalRecord)
FUNDAMENTAL_PRIMARY_KEY = ("symbol", "fiscal_period", "available_date")
