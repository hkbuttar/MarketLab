"""Tests for daily backtest valuation helpers."""

import csv
import gzip

from marketlab.backtest.engine import _apply_symbol, _security_reference


def test_adjusted_price_path_contributes_weighted_relative_value() -> None:
    periods = {("strategy", "2024-01-31"): [1.0, 1.0]}
    schedules = {"AAA": [("strategy", "2024-01-31", 0.5)]}
    calendar = ["2024-01-31", "2024-02-01", "2024-02-02"]

    _apply_symbol(
        "AAA",
        [("2024-02-01", 10.0), ("2024-02-02", 11.0)],
        schedules,
        periods,
        calendar,
        {date: index for index, date in enumerate(calendar)},
        {},
        0.7,
    )

    assert periods[("strategy", "2024-01-31")] == [1.0, 1.05]


def test_security_reference_excludes_exchange_test_symbols(tmp_path) -> None:
    crosswalk = tmp_path / "crosswalk.csv.gz"
    columns = (
        "symbol",
        "cik",
        "company_name",
        "exchange",
        "listing_start",
        "listing_end",
        "status",
        "source",
        "conflict",
    )
    with gzip.open(crosswalk, "wt", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "ZXZZT",
                "company_name": "NASDAQ TEST STOCK",
                "conflict": "false",
                "listing_end": "",
            }
        )

    delistings, excluded = _security_reference(crosswalk)

    assert not delistings
    assert excluded == {"ZXZZT"}
