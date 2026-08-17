"""Persist capacity diagnostics from canonical portfolio and liquidity artifacts."""

import csv
import gzip
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from marketlab.validation.capacity import capacity_curve, estimate_capacity


def build_capacity_report(
    targets_path: Path,
    panel_path: Path,
    output_path: Path,
    *,
    maximum_adv_participation: float = 0.10,
    liquidation_days: int = 1,
    aum_levels: tuple[float, ...] = (10_000_000, 25_000_000, 50_000_000, 100_000_000),
) -> dict[str, object]:
    """Build latest and worst-case capacity diagnostics for every strategy."""

    if output_path.exists():
        raise FileExistsError(f"capacity report already exists: {output_path}")
    targets = _read_targets(targets_path)
    liquidity = _read_liquidity(panel_path, targets)
    histories: dict[str, list[dict[str, object]]] = defaultdict(list)
    previous: dict[str, dict[str, float]] = defaultdict(dict)
    for date, strategy in sorted(targets):
        weights = targets[(date, strategy)]
        symbols = weights.keys() | previous[strategy].keys()
        changes = {
            symbol: weights.get(symbol, 0.0) - previous[strategy].get(symbol, 0.0)
            for symbol in symbols
            if weights.get(symbol, 0.0) != previous[strategy].get(symbol, 0.0)
        }
        if changes:
            date_liquidity = liquidity.get(date, {})
            missing = changes.keys() - date_liquidity.keys()
            if missing:
                raise ValueError(
                    f"liquidity missing for {date} {strategy}: {sorted(missing)[:5]}"
                )
            estimate = estimate_capacity(
                changes,
                date_liquidity,
                maximum_adv_participation=maximum_adv_participation,
                liquidation_days=liquidation_days,
            )
            histories[strategy].append(
                {
                    "date": date,
                    "maximum_aum": estimate.maximum_aum,
                    "binding_symbol": estimate.binding_securities[0].symbol,
                    "weight_changes": changes,
                    "liquidity": {symbol: date_liquidity[symbol] for symbol in changes},
                }
            )
        previous[strategy] = weights

    strategies: dict[str, object] = {}
    for strategy, history in sorted(histories.items()):
        latest = history[-1]
        curve = capacity_curve(
            latest.pop("weight_changes"),
            latest.pop("liquidity"),
            aum_levels,
            maximum_adv_participation=maximum_adv_participation,
            liquidation_days=liquidation_days,
        )
        historical = [float(item["maximum_aum"]) for item in history]
        for item in history[:-1]:
            item.pop("weight_changes")
            item.pop("liquidity")
        strategies[strategy] = {
            "latest": latest,
            "historical_minimum_aum": min(historical),
            "observations": len(history),
            "curve": [point.__dict__ for point in curve],
        }
    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "assumptions": {
            "maximum_adv_participation": maximum_adv_participation,
            "liquidation_days": liquidation_days,
        },
        "strategies": strategies,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _read_targets(path: Path) -> dict[tuple[str, str], dict[str, float]]:
    targets: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            targets[(row["date"], row["strategy"])][row["symbol"]] = float(
                row["weight"]
            )
    if not targets:
        raise ValueError("portfolio targets are empty")
    return dict(targets)


def _read_liquidity(
    path: Path, targets: dict[tuple[str, str], dict[str, float]]
) -> dict[str, dict[str, float]]:
    required: dict[str, set[str]] = defaultdict(set)
    previous: dict[str, set[str]] = defaultdict(set)
    for date, strategy in sorted(targets):
        current = set(targets[(date, strategy)])
        required[date].update(current | previous[strategy])
        previous[strategy] = current
    values: dict[str, dict[str, float]] = defaultdict(dict)
    last_seen: dict[str, float] = {}
    current_date = ""

    def fill_exits(date: str) -> None:
        for symbol in required.get(date, ()):
            if symbol not in values[date] and symbol in last_seen:
                values[date][symbol] = last_seen[symbol]

    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            date = row["date"]
            symbol = row["symbol"]
            if current_date and date != current_date:
                fill_exits(current_date)
            current_date = date
            if row["average_dollar_volume_21"]:
                dollar_volume = float(row["average_dollar_volume_21"])
                last_seen[symbol] = dollar_volume
                if symbol in required.get(date, ()):
                    values[date][symbol] = dollar_volume
    if current_date:
        fill_exits(current_date)
    return dict(values)
