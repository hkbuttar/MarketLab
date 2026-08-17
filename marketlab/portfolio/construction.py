"""Monthly target portfolio construction from investable factor ranks."""

import csv
import gzip
import json
import math
from pathlib import Path

from marketlab.features.preprocessing.investable import INVESTABLE_COLUMNS
from marketlab.portfolio.constraints import (
    apply_cash_buffer,
    filter_minimum_liquidity,
    limit_holdings,
)
from marketlab.portfolio.turnover import limit_turnover
from marketlab.portfolio.weighting import construct_weights
from marketlab.strategies.base import StrategyConfig, composite_score
from marketlab.strategies.low_volatility import LOW_VOLATILITY
from marketlab.strategies.momentum import MOMENTUM
from marketlab.strategies.multi_factor import QUALITY_VALUE_MOMENTUM

PORTFOLIO_COLUMNS = ("date", "strategy", "symbol", "score", "weight", "turnover")
DEFAULT_STRATEGIES = (MOMENTUM, LOW_VOLATILITY, QUALITY_VALUE_MOMENTUM)


def build_monthly_portfolios(
    panel: Path,
    output: Path,
    strategies: tuple[StrategyConfig, ...] = DEFAULT_STRATEGIES,
) -> dict[str, object]:
    """Construct constrained turnover-aware portfolios at each rebalance."""

    if output.exists():
        raise FileExistsError(f"portfolio output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    current: dict[str, dict[str, float]] = {config.name: {} for config in strategies}
    portfolio_rows = 0
    rebalances = 0
    turnover_totals = {config.name: 0.0 for config in strategies}
    try:
        with (
            gzip.open(panel, "rt", encoding="utf-8", newline="") as input_file,
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
        ):
            reader = csv.DictReader(input_file)
            if reader.fieldnames != list(INVESTABLE_COLUMNS):
                raise ValueError("investable panel columns are not canonical")
            writer = csv.DictWriter(output_file, fieldnames=PORTFOLIO_COLUMNS)
            writer.writeheader()
            current_date = ""
            rows: list[dict[str, str]] = []
            for row in reader:
                if current_date and row["date"] != current_date:
                    counts = _construct_date(
                        current_date, rows, strategies, current, writer
                    )
                    portfolio_rows += counts[0]
                    for name, value in counts[1].items():
                        turnover_totals[name] += value
                    rebalances += 1
                    rows = []
                current_date = row["date"]
                rows.append(row)
            if rows:
                counts = _construct_date(
                    current_date, rows, strategies, current, writer
                )
                portfolio_rows += counts[0]
                for name, value in counts[1].items():
                    turnover_totals[name] += value
                rebalances += 1
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    result: dict[str, object] = {
        "rebalances": rebalances,
        "portfolio_rows": portfolio_rows,
        "average_turnover": {
            name: total / rebalances for name, total in turnover_totals.items()
        },
    }
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _construct_date(
    date: str,
    rows: list[dict[str, str]],
    strategies: tuple[StrategyConfig, ...],
    current: dict[str, dict[str, float]],
    writer: csv.DictWriter,
) -> tuple[int, dict[str, float]]:
    written = 0
    turnovers: dict[str, float] = {}
    for config in strategies:
        scores = {
            row["symbol"]: score
            for row in rows
            if (score := composite_score(row, config)) is not None
        }
        scores = filter_minimum_liquidity(
            scores,
            {
                row["symbol"]: float(row["average_dollar_volume_21"])
                for row in rows
                if row["average_dollar_volume_21"]
            },
            config.minimum_dollar_volume,
        )
        minimum_holdings = math.ceil(1 / config.maximum_position)
        if len(scores) < minimum_holdings:
            turnovers[config.name] = 0.0
            for symbol, weight in sorted(current[config.name].items()):
                writer.writerow(
                    {
                        "date": date,
                        "strategy": config.name,
                        "symbol": symbol,
                        "score": _number(scores.get(symbol)),
                        "weight": _number(weight),
                        "turnover": "0",
                    }
                )
                written += 1
            continue
        selection_count = max(
            math.ceil(len(scores) * config.selection_fraction),
            minimum_holdings,
        )
        selected = dict(
            sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
                :selection_count
            ]
        )
        if config.maximum_holdings is not None:
            selected = limit_holdings(selected, config.maximum_holdings)
        target = construct_weights(
            selected, method=config.weighting, maximum_weight=config.maximum_position
        )
        target = apply_cash_buffer(target, config.cash_buffer)
        weights, turnover = limit_turnover(
            current[config.name], target, config.maximum_turnover
        )
        current[config.name] = weights
        turnovers[config.name] = turnover
        for symbol, weight in sorted(weights.items()):
            writer.writerow(
                {
                    "date": date,
                    "strategy": config.name,
                    "symbol": symbol,
                    "score": _number(scores.get(symbol)),
                    "weight": _number(weight),
                    "turnover": _number(turnover),
                }
            )
            written += 1
    return written, turnovers


def _number(value: float | None) -> str:
    return "" if value is None else format(value, ".15g")
