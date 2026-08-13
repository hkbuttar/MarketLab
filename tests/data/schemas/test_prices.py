"""Tests for the canonical daily-price schema."""

from datetime import datetime

import pytest

from marketlab.data.schemas import PRICE_COLUMNS, PRICE_PRIMARY_KEY, PriceRecord


def valid_price_values() -> dict[str, object]:
    return {
        "date": datetime(2024, 1, 2),
        "symbol": "AAPL",
        "open": 185.0,
        "high": 188.0,
        "low": 183.0,
        "close": 187.0,
        "adjusted_close": 186.5,
        "volume": 82_400_000,
    }


def test_price_schema_declares_columns_and_primary_key() -> None:
    assert PRICE_COLUMNS == (
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
    )
    assert PRICE_PRIMARY_KEY == ("date", "symbol")


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("date", "2024-01-02"),
        ("symbol", 123),
        ("open", 185),
        ("volume", "82400000"),
        ("volume", True),
    ],
)
def test_price_schema_rejects_invalid_types(
    field_name: str, invalid_value: object
) -> None:
    values = valid_price_values()
    values[field_name] = invalid_value

    with pytest.raises(TypeError, match=field_name):
        PriceRecord(**values)  # type: ignore[arg-type]
