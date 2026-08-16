"""Generate executable rebalance fills from monthly target weights."""

import csv
import gzip
import json
import math
from collections import defaultdict, deque
from pathlib import Path

from marketlab.backtest.accounting import Account
from marketlab.backtest.execution import rebalance_account
from marketlab.backtest.order import ExecutionQuote
from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.portfolio.construction import PORTFOLIO_COLUMNS

TRADE_COLUMNS = (
    "signal_date",
    "execution_date",
    "strategy",
    "symbol",
    "side",
    "quantity",
    "reference_price",
    "execution_price",
    "notional",
    "commission",
    "spread_cost",
    "impact_cost",
    "total_cost",
)


def generate_rebalance_trades(
    targets: Path, prices: Path, output: Path, initial_capital: float = 1_000_000
) -> dict[str, object]:
    """Simulate next-open fills for every strategy rebalance."""

    if output.exists():
        raise FileExistsError(f"trade output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    dates = _target_dates(targets)
    quotes = _execution_quotes(prices, dates)
    accounts: dict[str, Account] = {}
    trades = 0
    total_costs: dict[str, float] = defaultdict(float)
    try:
        with (
            gzip.open(targets, "rt", encoding="utf-8", newline="") as target_file,
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
        ):
            reader = csv.DictReader(target_file)
            if reader.fieldnames != list(PORTFOLIO_COLUMNS):
                raise ValueError("portfolio target columns are not canonical")
            writer = csv.DictWriter(output_file, fieldnames=TRADE_COLUMNS)
            writer.writeheader()
            key: tuple[str, str] | None = None
            weights: dict[str, float] = {}
            for row in reader:
                row_key = (row["date"], row["strategy"])
                if key is not None and row_key != key:
                    count = _execute_group(
                        key,
                        weights,
                        quotes,
                        accounts,
                        initial_capital,
                        writer,
                        total_costs,
                    )
                    trades += count
                    weights = {}
                key = row_key
                weights[row["symbol"]] = float(row["weight"])
            if key is not None:
                trades += _execute_group(
                    key, weights, quotes, accounts, initial_capital, writer, total_costs
                )
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    result: dict[str, object] = {
        "trades": trades,
        "ending_cash": {name: account.cash for name, account in accounts.items()},
        "ending_positions": {
            name: len(account.holdings) for name, account in accounts.items()
        },
        "total_costs": dict(total_costs),
    }
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _target_dates(path: Path) -> set[str]:
    dates: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PORTFOLIO_COLUMNS):
            raise ValueError("portfolio target columns are not canonical")
        for row in reader:
            dates.add(row["date"])
    return dates


def _execution_quotes(
    path: Path, signal_dates: set[str]
) -> dict[str, dict[str, ExecutionQuote]]:
    quotes: dict[str, dict[str, ExecutionQuote]] = defaultdict(dict)
    current_symbol = ""
    previous: dict[str, str] | None = None
    previous_adjustment_factor: float | None = None
    share_multiplier = 1.0
    dollar_volume: deque[float] = deque(maxlen=21)
    total = 0.0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PRICE_COLUMNS):
            raise ValueError("price columns do not match canonical schema")
        for row in reader:
            if row["symbol"] != current_symbol:
                current_symbol = row["symbol"]
                previous = None
                previous_adjustment_factor = None
                share_multiplier = 1.0
                dollar_volume = deque(maxlen=21)
                total = 0.0
            adjustment_factor = float(row["adjusted_close"]) / float(row["close"])
            if previous_adjustment_factor is not None:
                factor_change = adjustment_factor / previous_adjustment_factor
                if factor_change < 0.8 or factor_change > 1.25:
                    share_multiplier *= factor_change
            if previous is not None and previous["date"] in signal_dates:
                if len(dollar_volume) == 21:
                    average_dollar_volume = math.fsum(dollar_volume) / 21
                    if average_dollar_volume > 0:
                        quotes[previous["date"]][current_symbol] = ExecutionQuote(
                            execution_date=row["date"],
                            open_price=float(row["open"]),
                            average_dollar_volume=average_dollar_volume,
                            share_multiplier=share_multiplier,
                        )
                    share_multiplier = 1.0
            if len(dollar_volume) == 21:
                total -= dollar_volume[0]
            dollar = float(row["close"]) * float(row["volume"])
            dollar_volume.append(dollar)
            total += dollar
            previous = row
            previous_adjustment_factor = adjustment_factor
    return quotes


def _execute_group(
    key: tuple[str, str],
    weights: dict[str, float],
    quotes: dict[str, dict[str, ExecutionQuote]],
    accounts: dict[str, Account],
    initial_capital: float,
    writer: csv.DictWriter,
    total_costs: dict[str, float],
) -> int:
    signal_date, strategy = key
    account = accounts.setdefault(strategy, Account(initial_capital))
    date_quotes = quotes.get(signal_date, {})
    needed_symbols = weights.keys() | account.holdings.keys()
    strategy_quotes = {
        symbol: date_quotes[symbol]
        for symbol in needed_symbols
        if symbol in date_quotes
    }
    fills, _ = rebalance_account(account, weights, strategy_quotes)
    for fill in fills:
        quote = strategy_quotes[fill.symbol]
        total_costs[strategy] += fill.total_cost
        writer.writerow(
            {
                "signal_date": signal_date,
                "execution_date": quote.execution_date,
                "strategy": strategy,
                "symbol": fill.symbol,
                "side": "buy" if fill.quantity > 0 else "sell",
                "quantity": abs(fill.quantity),
                "reference_price": fill.reference_price,
                "execution_price": fill.execution_price,
                "notional": fill.notional,
                "commission": fill.commission,
                "spread_cost": fill.spread_cost,
                "impact_cost": fill.impact_cost,
                "total_cost": fill.total_cost,
            }
        )
    return len(fills)
