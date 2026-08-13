"""Tests for the canonical security metadata schema."""

import pytest

from marketlab.data.schemas import (
    SECURITY_COLUMNS,
    SECURITY_PRIMARY_KEY,
    SecurityRecord,
)


def test_security_schema_declares_columns_and_primary_key() -> None:
    assert SECURITY_COLUMNS == (
        "symbol",
        "company_name",
        "sector",
        "industry",
        "exchange",
    )
    assert SECURITY_PRIMARY_KEY == ("symbol",)


def test_security_schema_requires_strings() -> None:
    with pytest.raises(TypeError, match="exchange"):
        SecurityRecord(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            exchange=123,  # type: ignore[arg-type]
        )
