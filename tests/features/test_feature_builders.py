"""Tests for technical and point-in-time fundamental features."""

import csv
import gzip
from pathlib import Path

import pytest

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


def test_builds_backward_looking_trend_and_reversal_features(tmp_path: Path) -> None:
    source = tmp_path / "history.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        for index in range(220):
            writer.writerow(_price(f"2024-{index + 1:03}", "AAA", index + 1))
    output = tmp_path / "technical.csv.gz"

    build_daily_technical_features(source, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[4]["return_5d"] == ""
    assert rows[5]["return_5d"] == "5"
    assert rows[48]["trend_sma_50"] == ""
    assert float(rows[49]["trend_sma_50"]) == pytest.approx(50 / 25.5 - 1)
    assert rows[198]["trend_sma_200"] == ""
    assert float(rows[199]["trend_sma_200"]) == pytest.approx(200 / 100.5 - 1)
    assert rows[38]["return_20d_zscore"] == ""
    assert rows[39]["return_20d_zscore"] != ""


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


def test_builds_same_period_year_over_year_growth(tmp_path: Path) -> None:
    source = tmp_path / "growth.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
        writer.writeheader()
        for year, revenue in ((2022, 100), (2023, 125)):
            writer.writerow(
                {
                    "symbol": "AAA",
                    "fiscal_period": f"{year}-Q2",
                    "report_date": f"{year}-06-30",
                    "available_date": f"{year}-08-01T12:00:00Z",
                    "revenue": revenue,
                }
            )
    output = tmp_path / "growth_features.csv.gz"

    build_fundamental_features(source, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[1]["revenue_growth_yoy"] == "0.25"


def test_missing_fiscal_year_leaves_growth_empty(tmp_path: Path) -> None:
    source = tmp_path / "missing_year.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "AAA",
                "fiscal_period": "-Q1",
                "report_date": "2023-03-31",
                "available_date": "2023-05-01T12:00:00Z",
                "revenue": 100,
            }
        )
    output = tmp_path / "missing_year_features.csv.gz"

    build_fundamental_features(source, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        row = next(csv.DictReader(file))
    assert row["revenue_growth_yoy"] == ""


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
