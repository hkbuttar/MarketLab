"""Daily portfolio valuation and net-performance orchestration."""

import bisect
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.portfolio.construction import PORTFOLIO_COLUMNS

DAILY_RESULT_COLUMNS = (
    "date",
    "strategy",
    "gross_nav",
    "net_nav",
    "daily_return",
    "benchmark_nav",
    "cumulative_costs",
)


def run_daily_backtest(
    targets: Path,
    prices: Path,
    trades: Path,
    crosswalk: Path,
    output: Path,
    *,
    initial_capital: float = 1_000_000,
    delisting_recovery: float = 0.70,
    strategies: set[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    cost_bps: float | None = None,
) -> dict[str, object]:
    """Value monthly targets daily using adjusted returns and realized costs."""

    if output.exists():
        raise FileExistsError(f"backtest output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    calendar, benchmark = _benchmark_calendar(prices)
    date_index = {date: index for index, date in enumerate(calendar)}
    periods, schedules = _target_schedules(
        targets,
        calendar,
        date_index,
        strategies=strategies,
        start_date=start_date,
        end_date=end_date,
    )
    if not periods:
        raise ValueError("no portfolio targets match the requested backtest")
    delistings, excluded_symbols = _security_reference(crosswalk)
    for symbol in excluded_symbols:
        schedules.pop(symbol, None)
    _accumulate_symbol_paths(
        prices, schedules, periods, calendar, date_index, delistings, delisting_recovery
    )
    costs = _trade_costs(
        trades,
        cost_bps=cost_bps,
        capital_scale=initial_capital / 1_000_000,
    )
    summary: dict[str, object] = {}
    try:
        with partial.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=DAILY_RESULT_COLUMNS)
            writer.writeheader()
            for strategy in sorted({key[0] for key in periods}):
                result = _write_strategy(
                    strategy,
                    periods,
                    calendar,
                    benchmark,
                    costs,
                    initial_capital,
                    writer,
                )
                summary[strategy] = result
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def _benchmark_calendar(prices: Path) -> tuple[list[str], dict[str, float]]:
    calendar: list[str] = []
    benchmark: dict[str, float] = {}
    with gzip.open(prices, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PRICE_COLUMNS):
            raise ValueError("price columns do not match canonical schema")
        for row in reader:
            if row["symbol"] == "SPY":
                calendar.append(row["date"])
                benchmark[row["date"]] = float(row["adjusted_close"])
    if not calendar:
        raise ValueError("SPY benchmark calendar is unavailable")
    return calendar, benchmark


def _target_schedules(
    targets: Path,
    calendar: list[str],
    date_index: dict[str, int],
    *,
    strategies: set[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[
    dict[tuple[str, str], list[float]],
    dict[str, list[tuple[str, str, float]]],
]:
    periods: dict[tuple[str, str], list[float]] = {}
    schedules: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    signal_dates: dict[str, list[str]] = defaultdict(list)
    rows: list[dict[str, str]] = []
    with gzip.open(targets, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PORTFOLIO_COLUMNS):
            raise ValueError("portfolio target columns are not canonical")
        for row in reader:
            if strategies is not None and row["strategy"] not in strategies:
                continue
            if start_date is not None and row["date"] < start_date:
                continue
            if end_date is not None and row["date"] > end_date:
                continue
            rows.append(row)
            if (
                not signal_dates[row["strategy"]]
                or signal_dates[row["strategy"]][-1] != row["date"]
            ):
                signal_dates[row["strategy"]].append(row["date"])
    lengths: dict[tuple[str, str], int] = {}
    for strategy, dates in signal_dates.items():
        for position, signal in enumerate(dates):
            start = date_index[signal] + 1
            period_end = (
                date_index[dates[position + 1]]
                if position + 1 < len(dates)
                else len(calendar) - 1
            )
            if end_date is not None:
                period_end = min(
                    period_end, bisect.bisect_right(calendar, end_date) - 1
                )
            length = max(0, period_end - start + 1)
            periods[(strategy, signal)] = [1.0] * length
            lengths[(strategy, signal)] = length
    for row in rows:
        key = (row["strategy"], row["date"])
        if lengths[key]:
            schedules[row["symbol"]].append((*key, float(row["weight"])))
    return periods, dict(schedules)


def _accumulate_symbol_paths(
    prices: Path,
    schedules: dict[str, list[tuple[str, str, float]]],
    periods: dict[tuple[str, str], list[float]],
    calendar: list[str],
    date_index: dict[str, int],
    delistings: dict[str, str],
    recovery: float,
) -> None:
    with gzip.open(prices, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        current_symbol = ""
        rows: list[tuple[str, float]] = []
        for row in reader:
            if current_symbol and row["symbol"] != current_symbol:
                _apply_symbol(
                    current_symbol,
                    rows,
                    schedules,
                    periods,
                    calendar,
                    date_index,
                    delistings,
                    recovery,
                )
                rows = []
            current_symbol = row["symbol"]
            if current_symbol in schedules:
                rows.append((row["date"], float(row["adjusted_close"])))
        if current_symbol:
            _apply_symbol(
                current_symbol,
                rows,
                schedules,
                periods,
                calendar,
                date_index,
                delistings,
                recovery,
            )


def _apply_symbol(
    symbol: str,
    rows: list[tuple[str, float]],
    schedules: dict[str, list[tuple[str, str, float]]],
    periods: dict[tuple[str, str], list[float]],
    calendar: list[str],
    date_index: dict[str, int],
    delistings: dict[str, str],
    recovery: float,
) -> None:
    if symbol not in schedules or not rows:
        return
    dates = [row[0] for row in rows]
    prices = [row[1] for row in rows]
    delisting = delistings.get(symbol, "")
    for strategy, signal, weight in schedules[symbol]:
        if delisting and signal >= delisting:
            continue
        path = periods[(strategy, signal)]
        start_index = date_index[signal] + 1
        if not path:
            continue
        start_date = calendar[start_index]
        price_position = bisect.bisect_left(dates, start_date)
        if price_position >= len(rows):
            continue
        base = prices[price_position]
        last_relative = 1.0
        for offset in range(len(path)):
            date = calendar[start_index + offset]
            while price_position + 1 < len(rows) and dates[price_position + 1] <= date:
                price_position += 1
            if dates[price_position] <= date:
                last_relative = prices[price_position] / base
            relative = last_relative
            if delisting and dates[price_position] <= delisting < date:
                relative *= recovery
            path[offset] += weight * (relative - 1)


def _security_reference(path: Path) -> tuple[dict[str, str], set[str]]:
    result: dict[str, str] = {}
    excluded: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if "TEST STOCK" in row["company_name"].upper():
                excluded.add(row["symbol"])
            if row["conflict"] == "false" and row["listing_end"]:
                result[row["symbol"]] = max(
                    result.get(row["symbol"], ""), row["listing_end"]
                )
    return result, excluded


def _trade_costs(
    path: Path, *, cost_bps: float | None = None, capital_scale: float = 1.0
) -> dict[tuple[str, str], float]:
    costs: dict[tuple[str, str], float] = defaultdict(float)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            value = (
                float(row["total_cost"])
                if cost_bps is None
                else float(row["notional"]) * cost_bps / 10_000
            )
            costs[(row["strategy"], row["execution_date"])] += value * capital_scale
    return dict(costs)


def _write_strategy(
    strategy: str,
    periods: dict[tuple[str, str], list[float]],
    calendar: list[str],
    benchmark: dict[str, float],
    costs: dict[tuple[str, str], float],
    initial_capital: float,
    writer: csv.DictWriter,
) -> dict[str, float | int]:
    signals = sorted(signal for name, signal in periods if name == strategy)
    gross_start = initial_capital
    net_start = initial_capital
    cumulative_costs = 0.0
    previous_net = initial_capital
    first_date = calendar[calendar.index(signals[0]) + 1]
    benchmark_start = benchmark[first_date]
    observations = 0
    for signal in signals:
        path = periods[(strategy, signal)]
        start_index = calendar.index(signal) + 1
        period_costs = 0.0
        for offset, relative in enumerate(path):
            date = calendar[start_index + offset]
            daily_cost = costs.get((strategy, date), 0.0)
            period_costs += daily_cost
            cumulative_costs += daily_cost
            gross_nav = gross_start * relative
            net_nav = max(0.0, net_start * relative - period_costs)
            daily_return = net_nav / previous_net - 1 if previous_net else 0.0
            writer.writerow(
                {
                    "date": date,
                    "strategy": strategy,
                    "gross_nav": gross_nav,
                    "net_nav": net_nav,
                    "daily_return": daily_return,
                    "benchmark_nav": initial_capital
                    * benchmark[date]
                    / benchmark_start,
                    "cumulative_costs": cumulative_costs,
                }
            )
            previous_net = net_nav
            observations += 1
        if path:
            gross_start *= path[-1]
            net_start = max(0.0, net_start * path[-1] - period_costs)
    return {
        "observations": observations,
        "ending_gross_nav": gross_start,
        "ending_net_nav": net_start,
        "total_costs": cumulative_costs,
    }
