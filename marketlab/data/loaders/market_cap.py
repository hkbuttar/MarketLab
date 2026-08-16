"""Point-in-time market-cap enrichment for canonical fundamentals."""

import csv
import gzip
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS, PRICE_COLUMNS


def add_point_in_time_market_cap(
    fundamentals: Path, prices: Path, output: Path
) -> dict[str, int]:
    """Join each filing to the latest nonfuture close and reported shares."""

    if output.exists():
        raise FileExistsError(f"valued fundamentals already exist: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    if partial.exists():
        raise FileExistsError(f"partial valued fundamentals exist: {partial}")

    rows = _read_fundamentals(fundamentals)
    targets: dict[str, list[tuple[date, int, float]]] = defaultdict(list)
    missing_shares = 0
    for index, row in enumerate(rows):
        try:
            shares = float(row["shares_outstanding"])
        except ValueError:
            missing_shares += 1
            continue
        available_date = date.fromisoformat(row["available_date"][:10])
        targets[row["symbol"]].append((available_date, index, shares))
    for symbol_targets in targets.values():
        symbol_targets.sort()

    market_caps: dict[int, float] = {}
    _match_prices(prices, targets, market_caps)
    try:
        with gzip.open(partial, "wt", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FUNDAMENTAL_COLUMNS)
            writer.writeheader()
            for index, row in enumerate(rows):
                market_cap = market_caps.get(index)
                row["market_cap"] = (
                    format(market_cap, ".15g") if market_cap is not None else ""
                )
                writer.writerow(row)
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    result = {
        "rows": len(rows),
        "valued_rows": len(market_caps),
        "missing_shares": missing_shares,
        "missing_prior_price": len(rows) - missing_shares - len(market_caps),
    }
    metadata = output.with_suffix(output.suffix + ".metadata.json")
    metadata.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _read_fundamentals(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(FUNDAMENTAL_COLUMNS):
            raise ValueError("fundamental columns do not match the canonical schema")
        return list(reader)


def _match_prices(
    path: Path,
    targets: dict[str, list[tuple[date, int, float]]],
    market_caps: dict[int, float],
) -> None:
    current_symbol = ""
    current_targets: list[tuple[date, int, float]] = []
    target_index = 0
    previous_close: float | None = None

    def finish_symbol() -> None:
        nonlocal target_index
        if previous_close is None:
            return
        while target_index < len(current_targets):
            _, row_index, shares = current_targets[target_index]
            market_caps[row_index] = previous_close * shares
            target_index += 1

    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PRICE_COLUMNS):
            raise ValueError("price columns do not match the canonical schema")
        for row in reader:
            symbol = row["symbol"]
            if symbol != current_symbol:
                finish_symbol()
                current_symbol = symbol
                current_targets = targets.get(symbol, [])
                target_index = 0
                previous_close = None
            if not current_targets or target_index >= len(current_targets):
                continue
            price_date = date.fromisoformat(row["date"])
            while (
                target_index < len(current_targets)
                and current_targets[target_index][0] < price_date
            ):
                if previous_close is not None:
                    _, row_index, shares = current_targets[target_index]
                    market_caps[row_index] = previous_close * shares
                target_index += 1
            previous_close = float(row["close"])
            while (
                target_index < len(current_targets)
                and current_targets[target_index][0] == price_date
            ):
                _, row_index, shares = current_targets[target_index]
                market_caps[row_index] = previous_close * shares
                target_index += 1
        finish_symbol()
