"""Tests for loading canonical Alpha Vantage price snapshots."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from marketlab.data.loaders import InvalidSnapshotError, load_alpha_vantage_prices


def _write_snapshot(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_prices_in_canonical_date_order(tmp_path: Path) -> None:
    path = _write_snapshot(
        tmp_path / "SPY.json",
        {
            "Meta Data": {"2. Symbol": "spy"},
            "Time Series (Daily)": {
                "2024-01-03": {
                    "1. open": "472.00",
                    "2. high": "475.00",
                    "3. low": "471.00",
                    "4. close": "474.00",
                    "5. adjusted close": "473.50",
                    "6. volume": "1200",
                },
                "2024-01-02": {
                    "1. open": "470.00",
                    "2. high": "473.00",
                    "3. low": "469.00",
                    "4. close": "472.00",
                    "5. adjusted close": "471.50",
                    "6. volume": "1000",
                },
            },
        },
    )

    records = load_alpha_vantage_prices(path)

    assert [record.date for record in records] == [
        datetime(2024, 1, 2),
        datetime(2024, 1, 3),
    ]
    assert records[0].symbol == "SPY"
    assert records[0].adjusted_close == 471.5
    assert records[0].volume == 1000


def test_rejects_missing_time_series(tmp_path: Path) -> None:
    path = _write_snapshot(tmp_path / "bad.json", {"Meta Data": {"2. Symbol": "SPY"}})

    with pytest.raises(InvalidSnapshotError, match="missing price data"):
        load_alpha_vantage_prices(path)


def test_rejects_invalid_observation(tmp_path: Path) -> None:
    path = _write_snapshot(
        tmp_path / "bad.json",
        {
            "Meta Data": {"2. Symbol": "SPY"},
            "Time Series (Daily)": {"2024-01-02": {"1. open": "470.00"}},
        },
    )

    with pytest.raises(InvalidSnapshotError, match="2024-01-02"):
        load_alpha_vantage_prices(path)
