"""Tests for audited price-row cleaning."""

import csv
import gzip
from pathlib import Path

from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.data.validation import clean_price_dataset


def test_quarantines_invalid_price_without_mutating_source(tmp_path: Path) -> None:
    source = tmp_path / "prices.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        writer.writerow(_row("2024-01-02", low="9"))
        writer.writerow(_row("2024-01-03", low="0"))
    original = source.read_bytes()
    output = tmp_path / "clean.csv.gz"
    quarantine = tmp_path / "quarantine.csv.gz"

    result = clean_price_dataset(source, output, quarantine)

    assert source.read_bytes() == original
    assert result["accepted_rows"] == 1
    assert result["quarantined_rows"] == 1
    with gzip.open(quarantine, "rt", encoding="utf-8", newline="") as file:
        rejected = list(csv.DictReader(file))
    assert rejected[0]["date"] == "2024-01-03"
    assert rejected[0]["issues"] == "non_positive_price_or_volume"


def _row(date: str, *, low: str) -> dict[str, str]:
    return {
        "date": date,
        "symbol": "EXM",
        "open": "10",
        "high": "12",
        "low": low,
        "close": "11",
        "adjusted_close": "11",
        "volume": "100",
    }
