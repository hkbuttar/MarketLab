"""Tests for daily backtest valuation helpers."""

import csv
import gzip

from marketlab.backtest.engine import (
    _apply_symbol,
    _security_reference,
    _target_schedules,
    _trade_costs,
)


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


def test_target_schedule_filters_strategy_and_date_window(tmp_path) -> None:
    targets = tmp_path / "targets.csv.gz"
    columns = ("date", "strategy", "symbol", "score", "weight", "turnover")
    with gzip.open(targets, "wt", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for strategy in ("momentum", "low_volatility"):
            for signal in ("2024-01-31", "2024-02-29"):
                writer.writerow(
                    {
                        "date": signal,
                        "strategy": strategy,
                        "symbol": "AAA",
                        "score": 1,
                        "weight": 1,
                        "turnover": 0.2,
                    }
                )
    calendar = ["2024-01-31", "2024-02-01", "2024-02-29", "2024-03-01"]

    periods, schedules = _target_schedules(
        targets,
        calendar,
        {date: index for index, date in enumerate(calendar)},
        strategies={"momentum"},
        start_date="2024-02-01",
        end_date="2024-03-01",
    )

    assert periods == {("momentum", "2024-02-29"): [1.0]}
    assert schedules == {"AAA": [("momentum", "2024-02-29", 1.0)]}


def test_flat_trade_cost_scales_with_requested_capital(tmp_path) -> None:
    trades = tmp_path / "trades.csv.gz"
    with gzip.open(trades, "wt", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("strategy", "execution_date", "notional", "total_cost"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "strategy": "momentum",
                "execution_date": "2024-02-01",
                "notional": 100_000,
                "total_cost": 25,
            }
        )

    costs = _trade_costs(trades, cost_bps=10, capital_scale=2)

    assert costs == {("momentum", "2024-02-01"): 200.0}
