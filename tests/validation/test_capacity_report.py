"""Tests for persisted capacity reporting."""

import csv
import gzip
import json

import pytest

from marketlab.validation.capacity_report import build_capacity_report


def _gzip_csv(path, columns, rows) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_build_capacity_report_tracks_latest_and_historical_capacity(tmp_path) -> None:
    targets = tmp_path / "targets.csv.gz"
    panel = tmp_path / "panel.csv.gz"
    output = tmp_path / "capacity.json"
    _gzip_csv(
        targets,
        ("date", "strategy", "symbol", "weight"),
        [
            {"date": "2024-01-31", "strategy": "alpha", "symbol": "A", "weight": 0.5},
            {"date": "2024-01-31", "strategy": "alpha", "symbol": "B", "weight": 0.5},
            {"date": "2024-02-29", "strategy": "alpha", "symbol": "A", "weight": 0.4},
            {"date": "2024-02-29", "strategy": "alpha", "symbol": "B", "weight": 0.6},
        ],
    )
    _gzip_csv(
        panel,
        ("date", "symbol", "average_dollar_volume_21"),
        [
            {
                "date": "2024-01-31",
                "symbol": "A",
                "average_dollar_volume_21": 10_000_000,
            },
            {
                "date": "2024-01-31",
                "symbol": "B",
                "average_dollar_volume_21": 20_000_000,
            },
            {
                "date": "2024-02-29",
                "symbol": "A",
                "average_dollar_volume_21": 10_000_000,
            },
            {
                "date": "2024-02-29",
                "symbol": "C",
                "average_dollar_volume_21": 30_000_000,
            },
        ],
    )

    result = build_capacity_report(targets, panel, output, aum_levels=(5_000_000,))

    strategy = result["strategies"]["alpha"]
    assert strategy["latest"]["date"] == "2024-02-29"
    assert strategy["latest"]["maximum_aum"] == pytest.approx(10_000_000)
    assert strategy["historical_minimum_aum"] == pytest.approx(2_000_000)
    assert strategy["observations"] == 2
    assert strategy["curve"][0]["feasible"] is True
    assert json.loads(output.read_text())["strategies"]["alpha"]["observations"] == 2


def test_build_capacity_report_rejects_missing_liquidity(tmp_path) -> None:
    targets = tmp_path / "targets.csv.gz"
    panel = tmp_path / "panel.csv.gz"
    _gzip_csv(
        targets,
        ("date", "strategy", "symbol", "weight"),
        [{"date": "2024-01-31", "strategy": "alpha", "symbol": "A", "weight": 1}],
    )
    _gzip_csv(panel, ("date", "symbol", "average_dollar_volume_21"), [])

    with pytest.raises(ValueError, match="liquidity missing"):
        build_capacity_report(targets, panel, tmp_path / "capacity.json")
