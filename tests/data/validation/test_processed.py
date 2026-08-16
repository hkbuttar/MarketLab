"""Tests for streaming processed-data validation."""

import csv
import gzip
from pathlib import Path

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS, PRICE_COLUMNS
from marketlab.data.validation import validate_processed_data


def test_validates_clean_processed_data(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv.gz"
    with gzip.open(prices, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "date": "2024-01-02",
                "symbol": "EXM",
                "open": 10,
                "high": 12,
                "low": 9,
                "close": 11,
                "adjusted_close": 11,
                "volume": 100,
            }
        )
    fundamentals = tmp_path / "fundamentals.csv.gz"
    with gzip.open(fundamentals, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "EXM",
                "fiscal_period": "2023-FY",
                "report_date": "2023-12-31",
                "available_date": "2024-02-01T12:00:00Z",
                "assets": 100,
                "shares_outstanding": 10,
            }
        )

    result = validate_processed_data(prices, fundamentals, tmp_path / "report.json")

    assert result["status"] == "passed"
    assert result["coverage"]["symbols_with_both"] == 1
    assert result["fundamentals"]["missing"]["market_cap"] == 1
