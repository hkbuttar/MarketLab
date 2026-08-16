"""Tests for technical and point-in-time fundamental features."""

import csv
import gzip
from pathlib import Path

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS, PRICE_COLUMNS
from marketlab.features.fundamental import build_fundamental_features
from marketlab.features.technical import build_daily_technical_features


def test_builds_returns_without_crossing_symbols(tmp_path: Path) -> None:
    source = tmp_path / "prices.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerow(_price("2024-01-01", "AAA", 10))
        writer.writerow(_price("2024-01-02", "AAA", 11))
        writer.writerow(_price("2024-01-01", "BBB", 20))
    output = tmp_path / "technical.csv.gz"

    build_daily_technical_features(source, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[1]["return_1d"] == "0.1"
    assert rows[2]["return_1d"] == ""


def test_builds_fundamental_ratios(tmp_path: Path) -> None:
    source = tmp_path / "fundamentals.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "AAA",
                "fiscal_period": "2023-FY",
                "report_date": "2023-12-31",
                "available_date": "2024-02-01T12:00:00Z",
                "market_cap": 200,
                "book_value": 100,
                "net_income": 20,
                "assets": 400,
                "debt": 80,
            }
        )
    output = tmp_path / "ratios.csv.gz"

    build_fundamental_features(source, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        row = next(csv.DictReader(file))
    assert row["book_to_market"] == "0.5"
    assert row["return_on_assets"] == "0.05"
    assert row["leverage"] == "0.2"


def _price(day: str, symbol: str, close: int) -> dict[str, object]:
    return {
        "date": day,
        "symbol": symbol,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close,
        "volume": 100,
    }
