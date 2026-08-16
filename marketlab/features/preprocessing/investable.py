"""Investable-universe screens and robust cross-sectional preprocessing."""

import csv
import gzip
import json
import math
from collections import deque
from pathlib import Path

from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.factors.information_coefficient import spearman_ic
from marketlab.factors.quantiles import quantile_mean_returns
from marketlab.factors.ranking import percentile_ranks, quantile
from marketlab.factors.research import FACTOR_NAMES, PANEL_COLUMNS

MINIMUM_PRICE = 5.0
MINIMUM_AVERAGE_DOLLAR_VOLUME = 1_000_000.0
WINSOR_LOWER = 0.01
WINSOR_UPPER = 0.99
INVESTABLE_COLUMNS = (
    "date",
    "symbol",
    "close",
    "average_dollar_volume_21",
    "forward_return_21",
    *(f"{factor}_winsorized" for factor in FACTOR_NAMES),
    *(f"{factor}_rank" for factor in FACTOR_NAMES),
    *(f"{factor}_quantile" for factor in FACTOR_NAMES),
)


def build_investable_factor_research(
    panel: Path,
    prices: Path,
    output: Path,
    ic_output: Path,
    quantile_output: Path,
) -> dict[str, int]:
    """Screen, winsorize, rerank, and diagnose monthly factor observations."""

    for path in (output, ic_output, quantile_output):
        if path.exists():
            raise FileExistsError(f"preprocessed output already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    dates = _panel_dates(panel)
    controls = _market_controls(prices, dates)
    output_partial = output.with_name(f"{output.name}.part")
    ic_partial = ic_output.with_name(f"{ic_output.name}.part")
    quantile_partial = quantile_output.with_name(f"{quantile_output.name}.part")
    input_rows = 0
    eligible_rows = 0
    ic_rows = 0
    quantile_rows = 0
    try:
        with (
            gzip.open(panel, "rt", encoding="utf-8", newline="") as input_file,
            gzip.open(output_partial, "wt", encoding="utf-8", newline="") as out_file,
            ic_partial.open("w", encoding="utf-8", newline="") as ic_file,
            quantile_partial.open("w", encoding="utf-8", newline="") as q_file,
        ):
            reader = csv.DictReader(input_file)
            if reader.fieldnames != list(PANEL_COLUMNS):
                raise ValueError("monthly factor panel columns are not canonical")
            writer = csv.DictWriter(out_file, fieldnames=INVESTABLE_COLUMNS)
            ic_writer = csv.DictWriter(
                ic_file, fieldnames=("date", "factor", "observations", "ic")
            )
            q_writer = csv.DictWriter(
                q_file,
                fieldnames=("date", "factor", "quantile", "mean_forward_return"),
            )
            writer.writeheader()
            ic_writer.writeheader()
            q_writer.writeheader()
            current_date = ""
            rows: list[dict[str, str]] = []
            for row in reader:
                input_rows += 1
                if current_date and row["date"] != current_date:
                    counts = _process_date(rows, controls, writer, ic_writer, q_writer)
                    eligible_rows += counts[0]
                    ic_rows += counts[1]
                    quantile_rows += counts[2]
                    rows = []
                current_date = row["date"]
                rows.append(row)
            if rows:
                counts = _process_date(rows, controls, writer, ic_writer, q_writer)
                eligible_rows += counts[0]
                ic_rows += counts[1]
                quantile_rows += counts[2]
        output_partial.replace(output)
        ic_partial.replace(ic_output)
        quantile_partial.replace(quantile_output)
    except BaseException:
        for path in (output_partial, ic_partial, quantile_partial):
            path.unlink(missing_ok=True)
        raise
    result = {
        "input_rows": input_rows,
        "eligible_rows": eligible_rows,
        "excluded_rows": input_rows - eligible_rows,
        "ic_rows": ic_rows,
        "quantile_rows": quantile_rows,
    }
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def winsorize(values: list[float | None]) -> list[float | None]:
    """Clip finite values to cross-sectional 1st/99th percentile bounds."""

    finite = sorted(
        value for value in values if value is not None and math.isfinite(value)
    )
    if len(finite) < 2:
        return values.copy()
    lower = _percentile(finite, WINSOR_LOWER)
    upper = _percentile(finite, WINSOR_UPPER)
    return [
        None if value is None else min(upper, max(lower, value)) for value in values
    ]


def _panel_dates(path: Path) -> set[str]:
    dates: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PANEL_COLUMNS):
            raise ValueError("monthly factor panel columns are not canonical")
        for row in reader:
            dates.add(row["date"])
    return dates


def _market_controls(
    prices: Path, rebalance_dates: set[str]
) -> dict[tuple[str, str], tuple[float, float]]:
    controls: dict[tuple[str, str], tuple[float, float]] = {}
    current_symbol = ""
    dollar_volume: deque[float] = deque(maxlen=21)
    total = 0.0
    with gzip.open(prices, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(PRICE_COLUMNS):
            raise ValueError("price columns do not match the canonical schema")
        for row in reader:
            if row["symbol"] != current_symbol:
                current_symbol = row["symbol"]
                dollar_volume = deque(maxlen=21)
                total = 0.0
            if len(dollar_volume) == 21:
                total -= dollar_volume[0]
            close = float(row["close"])
            dollar = close * float(row["volume"])
            dollar_volume.append(dollar)
            total += dollar
            if row["date"] in rebalance_dates and len(dollar_volume) == 21:
                controls[(row["date"], row["symbol"])] = (close, total / 21)
    return controls


def _process_date(
    rows: list[dict[str, str]],
    controls: dict[tuple[str, str], tuple[float, float]],
    writer: csv.DictWriter,
    ic_writer: csv.DictWriter,
    q_writer: csv.DictWriter,
) -> tuple[int, int, int]:
    eligible: list[tuple[dict[str, str], float, float]] = []
    for row in rows:
        control = controls.get((row["date"], row["symbol"]))
        if control is None or not row["forward_return_21"]:
            continue
        close, average_dollar_volume = control
        liquid = average_dollar_volume >= MINIMUM_AVERAGE_DOLLAR_VOLUME
        if close >= MINIMUM_PRICE and liquid:
            eligible.append((row, close, average_dollar_volume))
    forward = winsorize([_float(item[0]["forward_return_21"]) for item in eligible])
    factor_values: dict[str, list[float | None]] = {}
    factor_ranks: dict[str, list[float | None]] = {}
    factor_quantiles: dict[str, list[int | None]] = {}
    ic_count = 0
    q_count = 0
    for factor in FACTOR_NAMES:
        values = winsorize([_float(item[0][factor]) for item in eligible])
        ranks = percentile_ranks(values)
        buckets = [quantile(rank) for rank in ranks]
        factor_values[factor] = values
        factor_ranks[factor] = ranks
        factor_quantiles[factor] = buckets
        ic = spearman_ic(values, forward)
        observations = sum(
            value is not None and target is not None
            for value, target in zip(values, forward, strict=True)
        )
        ic_writer.writerow(
            {
                "date": rows[0]["date"],
                "factor": factor,
                "observations": observations,
                "ic": _number(ic),
            }
        )
        ic_count += 1
        for bucket, mean_return in quantile_mean_returns(buckets, forward).items():
            q_writer.writerow(
                {
                    "date": rows[0]["date"],
                    "factor": factor,
                    "quantile": bucket,
                    "mean_forward_return": _number(mean_return),
                }
            )
            q_count += 1
    for index, (row, close, average_dollar_volume) in enumerate(eligible):
        output = {
            "date": row["date"],
            "symbol": row["symbol"],
            "close": _number(close),
            "average_dollar_volume_21": _number(average_dollar_volume),
            "forward_return_21": _number(forward[index]),
        }
        for factor in FACTOR_NAMES:
            output[f"{factor}_winsorized"] = _number(factor_values[factor][index])
            output[f"{factor}_rank"] = _number(factor_ranks[factor][index])
            output[f"{factor}_quantile"] = factor_quantiles[factor][index] or ""
        writer.writerow(output)
    return len(eligible), ic_count, q_count


def _percentile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _float(value: str) -> float | None:
    return float(value) if value else None


def _number(value: float | None) -> str:
    return "" if value is None else format(value, ".15g")
