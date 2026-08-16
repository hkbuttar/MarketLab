"""Tests for processed price-dataset construction."""

import csv
import gzip
import json
from pathlib import Path

from marketlab.data.loaders import latest_price_snapshot, write_price_dataset


def _snapshot(raw_root: Path, symbol: str, timestamp: str, close: str) -> Path:
    path = raw_root / "prices" / "alpha_vantage" / symbol / timestamp / f"{symbol}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "Meta Data": {"2. Symbol": symbol},
                "Time Series (Daily)": {
                    "2024-01-02": {
                        "1. open": "10",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": close,
                        "5. adjusted close": close,
                        "6. volume": "100",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_selects_latest_snapshot(tmp_path: Path) -> None:
    _snapshot(tmp_path, "SPY", "2024-01-01T000000Z", "10")
    latest = _snapshot(tmp_path, "SPY", "2024-01-02T000000Z", "11")

    assert latest_price_snapshot(tmp_path, "SPY") == latest


def test_writes_compressed_dataset_and_missing_symbol_manifest(
    tmp_path: Path,
) -> None:
    _snapshot(tmp_path, "SPY", "2024-01-01T000000Z", "10")
    output = tmp_path / "processed" / "prices.csv.gz"

    result = write_price_dataset(
        raw_root=tmp_path, output_path=output, symbols=["MISSING", "SPY"]
    )

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["symbol"] == "SPY"
    assert rows[0]["close"] == "10.0"
    assert result == {
        "requested_symbols": 2,
        "loaded_symbols": 1,
        "missing_symbols": ["MISSING"],
        "rows": 1,
    }
    assert output.with_suffix(".gz.metadata.json").exists()
