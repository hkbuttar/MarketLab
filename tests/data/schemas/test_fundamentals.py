"""Tests for the canonical point-in-time fundamental schema."""

from datetime import datetime

import pytest

from marketlab.data.schemas import (
    FUNDAMENTAL_COLUMNS,
    FUNDAMENTAL_PRIMARY_KEY,
    FundamentalRecord,
)


def valid_fundamental_values() -> dict[str, object]:
    return {
        "symbol": "AAPL",
        "fiscal_period": "2024-Q1",
        "report_date": datetime(2023, 12, 30),
        "available_date": datetime(2024, 2, 1),
        "market_cap": 2.9e12,
        "book_value": 74.1e9,
        "net_income": 33.9e9,
        "revenue": 119.6e9,
        "gross_profit": 54.9e9,
        "assets": 353.5e9,
        "debt": 108.0e9,
        "free_cash_flow": 37.5e9,
        "shares_outstanding": 15.4e9,
    }


def test_fundamental_schema_declares_columns_and_primary_key() -> None:
    assert FUNDAMENTAL_COLUMNS == (
        "symbol",
        "fiscal_period",
        "report_date",
        "available_date",
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
    assert FUNDAMENTAL_PRIMARY_KEY == ("symbol", "fiscal_period", "available_date")


def test_fundamental_schema_preserves_point_in_time_dates() -> None:
    record = FundamentalRecord(**valid_fundamental_values())  # type: ignore[arg-type]

    assert record.report_date == datetime(2023, 12, 30)
    assert record.available_date == datetime(2024, 2, 1)


def test_fundamental_schema_allows_missing_numeric_values() -> None:
    values = valid_fundamental_values()
    values["book_value"] = None

    record = FundamentalRecord(**values)  # type: ignore[arg-type]

    assert record.book_value is None


@pytest.mark.parametrize("field_name", ["report_date", "available_date"])
def test_fundamental_schema_requires_datetime_fields(field_name: str) -> None:
    values = valid_fundamental_values()
    values[field_name] = "2024-02-01"

    with pytest.raises(TypeError, match=field_name):
        FundamentalRecord(**values)  # type: ignore[arg-type]


def test_fundamental_schema_rejects_non_numeric_values() -> None:
    values = valid_fundamental_values()
    values["market_cap"] = "2.9T"

    with pytest.raises(TypeError, match="market_cap"):
        FundamentalRecord(**values)  # type: ignore[arg-type]
