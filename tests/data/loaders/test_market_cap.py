"""Tests for point-in-time market-cap enrichment."""

import csv
import gzip
from pathlib import Path

from marketlab.data.loaders.market_cap import add_point_in_time_market_cap
from marketlab.data.schemas import FUNDAMENTAL_COLUMNS, PRICE_COLUMNS


def test_uses_latest_close_before_weekend_availability(tmp_path: Path) -> None:
    fundamentals = tmp_path / "fundamentals.csv.gz"
    with gzip.open(fundamentals, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "EXM",
                "fiscal_period": "2023-FY",
                "report_date": "2023-12-31",
                "available_date": "2024-01-06T12:00:00Z",
                "shares_outstanding": "10",
            }
        )
    prices = tmp_path / "prices.csv.gz"
    with gzip.open(prices, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerow(_price("2024-01-05", 12))
        writer.writerow(_price("2024-01-08", 20))

    output = tmp_path / "valued.csv.gz"
    result = add_point_in_time_market_cap(fundamentals, prices, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        row = next(csv.DictReader(file))
    assert result["valued_rows"] == 1
    assert row["market_cap"] == "120"


def _price(day: str, close: int) -> dict[str, object]:
    return {
        "date": day,
        "symbol": "EXM",
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close,
        "volume": 100,
    }
