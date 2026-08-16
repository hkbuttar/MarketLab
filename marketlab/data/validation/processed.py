"""Streaming validation for canonical processed datasets."""

import csv
import gzip
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS, PRICE_COLUMNS
from marketlab.data.schemas.fundamentals import FUNDAMENTAL_NUMERIC_COLUMNS

EXAMPLE_LIMIT = 20


def validate_processed_data(
    prices: Path, fundamentals: Path, report_path: Path
) -> dict[str, object]:
    """Validate prices, fundamentals, and cross-dataset symbol coverage."""

    price_result, price_symbols = _validate_prices(prices)
    fundamental_result, fundamental_symbols = _validate_fundamentals(fundamentals)
    report: dict[str, object] = {
        "status": (
            "failed"
            if price_result["errors"] or fundamental_result["errors"]
            else "passed"
        ),
        "prices": price_result,
        "fundamentals": fundamental_result,
        "coverage": {
            "price_symbols": len(price_symbols),
            "fundamental_symbols": len(fundamental_symbols),
            "symbols_with_both": len(price_symbols & fundamental_symbols),
            "fundamental_symbols_without_prices": sorted(
                fundamental_symbols - price_symbols
            ),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    partial = report_path.with_name(f"{report_path.name}.part")
    partial.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(report_path)
    return report


def _validate_prices(path: Path) -> tuple[dict[str, object], set[str]]:
    errors: Counter[str] = Counter()
    examples: list[dict[str, str]] = []
    symbols: set[str] = set()
    completed_symbols: set[str] = set()
    previous_symbol = ""
    previous_date = ""
    rows = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        _require_columns(reader.fieldnames, PRICE_COLUMNS, "prices")
        for row in reader:
            rows += 1
            symbol = row["symbol"]
            date = row["date"]
            symbols.add(symbol)
            if symbol != previous_symbol:
                if previous_symbol:
                    completed_symbols.add(previous_symbol)
                if symbol in completed_symbols:
                    _record(errors, examples, "non_contiguous_symbol", row)
                previous_symbol = symbol
                previous_date = ""
            if previous_date and date <= previous_date:
                _record(errors, examples, "duplicate_or_unsorted_key", row)
            previous_date = date
            for issue in price_row_issues(row):
                _record(errors, examples, issue, row)
    return {
        "rows": rows,
        "symbols": len(symbols),
        "errors": dict(errors),
        "examples": examples,
    }, symbols


def price_row_issues(row: dict[str, str]) -> list[str]:
    """Return deterministic reason codes for an invalid canonical price row."""

    try:
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        adjusted = float(row["adjusted_close"])
        volume = float(row["volume"])
    except (KeyError, ValueError):
        return ["invalid_numeric_value"]
    values = (open_price, high, low, close, adjusted, volume)
    issues: list[str] = []
    if not all(math.isfinite(value) for value in values):
        issues.append("non_finite_value")
        return issues
    if min(open_price, high, low, close, adjusted) <= 0 or volume < 0:
        issues.append("non_positive_price_or_volume")
    if low > min(open_price, close) or high < max(open_price, close):
        issues.append("invalid_ohlc_relationship")
    return issues


def _validate_fundamentals(path: Path) -> tuple[dict[str, object], set[str]]:
    errors: Counter[str] = Counter()
    warnings: Counter[str] = Counter()
    examples: list[dict[str, str]] = []
    missing: Counter[str] = Counter()
    symbols: set[str] = set()
    keys: set[tuple[str, str, str]] = set()
    rows = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        _require_columns(reader.fieldnames, FUNDAMENTAL_COLUMNS, "fundamentals")
        for row in reader:
            rows += 1
            symbols.add(row["symbol"])
            key = (row["symbol"], row["fiscal_period"], row["available_date"])
            if key in keys:
                _record(errors, examples, "duplicate_primary_key", row)
            keys.add(key)
            try:
                report_date = datetime.fromisoformat(row["report_date"])
                available_date = datetime.fromisoformat(
                    row["available_date"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except ValueError:
                _record(errors, examples, "invalid_date", row)
            else:
                if available_date.date() < report_date.date():
                    _record(errors, examples, "available_before_report", row)
            for column in FUNDAMENTAL_NUMERIC_COLUMNS:
                value = row[column]
                if not value:
                    missing[column] += 1
                    continue
                try:
                    numeric = float(value)
                except ValueError:
                    _record(errors, examples, f"invalid_{column}", row)
                    continue
                if not math.isfinite(numeric):
                    _record(errors, examples, f"non_finite_{column}", row)
                if column in {"assets", "shares_outstanding"} and numeric <= 0:
                    warnings[f"non_positive_{column}"] += 1
    return {
        "rows": rows,
        "symbols": len(symbols),
        "errors": dict(errors),
        "warnings": dict(warnings),
        "missing": dict(missing),
        "examples": examples,
    }, symbols


def _require_columns(
    actual: list[str] | None, expected: tuple[str, ...], dataset: str
) -> None:
    if actual != list(expected):
        raise ValueError(f"{dataset} columns do not match the canonical schema")


def _record(
    counts: Counter[str],
    examples: list[dict[str, str]],
    issue: str,
    row: dict[str, str],
) -> None:
    counts[issue] += 1
    if len(examples) < EXAMPLE_LIMIT:
        examples.append(
            {
                "issue": issue,
                "symbol": row.get("symbol", ""),
                "date": row.get("date", row.get("report_date", "")),
            }
        )
