"""Tests for portfolio exposure analysis."""

import csv
import gzip
import json

import pytest

from marketlab.attribution.exposures import FACTOR_RANKS, build_exposure_report


def _write_gzip(path, columns, rows) -> None:
    with gzip.open(path, "wt", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_exposure_report_aggregates_sectors_factors_and_concentration(
    tmp_path,
) -> None:
    overview = tmp_path / "overview"
    for symbol, sector in (("AAA", "TECHNOLOGY"), ("BBB", "HEALTHCARE")):
        directory = overview / f"{symbol}_overview" / "snapshot"
        directory.mkdir(parents=True)
        (directory / f"{symbol}_overview.json").write_text(
            json.dumps({"Symbol": symbol, "Sector": sector})
        )
    targets = tmp_path / "targets.csv.gz"
    _write_gzip(
        targets,
        ("date", "strategy", "symbol", "weight"),
        [
            {
                "date": "2024-01-31",
                "strategy": "test",
                "symbol": "AAA",
                "weight": 0.6,
            },
            {
                "date": "2024-01-31",
                "strategy": "test",
                "symbol": "BBB",
                "weight": 0.4,
            },
        ],
    )
    panel = tmp_path / "panel.csv.gz"
    columns = ("date", "symbol", "average_dollar_volume_21", *FACTOR_RANKS)
    _write_gzip(
        panel,
        columns,
        [
            {
                **{column: 0.75 for column in FACTOR_RANKS},
                "date": "2024-01-31",
                "symbol": "AAA",
                "average_dollar_volume_21": 75,
            },
            {
                **{column: 0.25 for column in FACTOR_RANKS},
                "date": "2024-01-31",
                "symbol": "BBB",
                "average_dollar_volume_21": 25,
            },
        ],
    )
    regression = tmp_path / "regression.json"
    regression.write_text(json.dumps({"test": {"coefficients": {"market": 0.8}}}))

    report = build_exposure_report(
        targets, panel, overview, regression, tmp_path / "output"
    )

    strategy = report["strategies"]["test"]
    assert strategy["market_beta"] == pytest.approx(0.8)
    assert strategy["average_hhi"] == pytest.approx(0.52)
    assert strategy["latest_sector_weights"] == {
        "HEALTHCARE": 0.4,
        "TECHNOLOGY": 0.6,
    }
    assert (tmp_path / "output" / "sector_exposures.csv").exists()
    assert (tmp_path / "output" / "factor_exposures.csv").exists()
