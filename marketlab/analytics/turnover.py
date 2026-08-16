"""Trading and turnover diagnostics."""

import csv
import gzip
from collections import defaultdict
from pathlib import Path


def trading_statistics(path: Path) -> dict[str, dict[str, float | int]]:
    """Aggregate realized trading activity by strategy."""

    result: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "trade_count": 0,
            "traded_notional": 0.0,
            "transaction_costs": 0.0,
        }
    )
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            values = result[row["strategy"]]
            values["trade_count"] += 1
            values["traded_notional"] += float(row["notional"])
            values["transaction_costs"] += float(row["total_cost"])
    return dict(result)


def portfolio_statistics(path: Path) -> dict[str, dict[str, float]]:
    """Aggregate monthly target holdings and one-way turnover by strategy."""

    holdings: dict[tuple[str, str], int] = defaultdict(int)
    turnover: dict[tuple[str, str], float] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            key = (row["strategy"], row["date"])
            holdings[key] += 1
            turnover[key] = float(row["turnover"])
    strategies = sorted({strategy for strategy, _ in holdings})
    result: dict[str, dict[str, float]] = {}
    for strategy in strategies:
        counts = [value for (name, _), value in holdings.items() if name == strategy]
        values = [value for (name, _), value in turnover.items() if name == strategy]
        average_turnover = sum(values) / len(values)
        result[strategy] = {
            "average_holdings": sum(counts) / len(counts),
            "average_monthly_turnover": average_turnover,
            "annualized_turnover": average_turnover * 12.0,
        }
    return result
