"""Factor tear-sheet assembly."""

import csv
import gzip
import json
import math
import statistics
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path

from marketlab.factors.correlations import pearson_correlation
from marketlab.factors.research import FACTOR_NAMES
from marketlab.features.preprocessing.investable import INVESTABLE_COLUMNS


def build_factor_tear_sheet(
    panel: Path,
    ic_path: Path,
    quantile_path: Path,
    summary_path: Path,
    rolling_ic_path: Path,
    turnover_path: Path,
    correlation_path: Path,
) -> dict[str, object]:
    """Build compact stability and redundancy diagnostics for each factor."""

    for path in (summary_path, rolling_ic_path, turnover_path, correlation_path):
        if path.exists():
            raise FileExistsError(f"factor tear-sheet output exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    ic_values, rolling_rows = _ic_statistics(ic_path)
    quantile_summary = _quantile_statistics(quantile_path)
    turnover_summary, turnover_rows, correlations = _panel_statistics(panel)
    summary = {
        "information_coefficient": {
            factor: _series_summary(values) for factor, values in ic_values.items()
        },
        "quantiles": quantile_summary,
        "top_quantile_turnover": turnover_summary,
        "factor_correlations": {
            f"{first}__{second}": values
            for (first, second), values in correlations.items()
        },
    }
    _write_json_atomic(summary_path, summary)
    _write_csv_atomic(
        rolling_ic_path,
        ("date", "factor", "rolling_12m_ic"),
        rolling_rows,
    )
    _write_csv_atomic(
        turnover_path,
        ("date", "factor", "top_quantile_turnover"),
        turnover_rows,
    )
    correlation_rows = [
        {
            "factor_a": first,
            "factor_b": second,
            "months": values["months"],
            "mean_correlation": values["mean_correlation"],
        }
        for (first, second), values in correlations.items()
    ]
    _write_csv_atomic(
        correlation_path,
        ("factor_a", "factor_b", "months", "mean_correlation"),
        correlation_rows,
    )
    return summary


def _ic_statistics(
    path: Path,
) -> tuple[dict[str, list[float]], list[dict[str, object]]]:
    values: dict[str, list[float]] = defaultdict(list)
    windows: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=12))
    rolling: list[dict[str, object]] = []
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if not row["ic"]:
                continue
            factor = row["factor"]
            value = float(row["ic"])
            values[factor].append(value)
            windows[factor].append(value)
            rolling.append(
                {
                    "date": row["date"],
                    "factor": factor,
                    "rolling_12m_ic": (
                        _number(statistics.fmean(windows[factor]))
                        if len(windows[factor]) == 12
                        else ""
                    ),
                }
            )
    return dict(values), rolling


def _quantile_statistics(path: Path) -> dict[str, dict[str, float | int | None]]:
    by_factor_date: dict[str, dict[str, dict[int, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            by_factor_date[row["factor"]][row["date"]][int(row["quantile"])] = float(
                row["mean_forward_return"]
            )
    result: dict[str, dict[str, float | int | None]] = {}
    for factor, dates in by_factor_date.items():
        spreads: list[float] = []
        monotonicity: list[float] = []
        for quantiles in dates.values():
            if 1 in quantiles and 5 in quantiles:
                spreads.append(quantiles[5] - quantiles[1])
            ordered = sorted(quantiles)
            correlation = pearson_correlation(
                [float(bucket) for bucket in ordered],
                [quantiles[bucket] for bucket in ordered],
            )
            if correlation is not None:
                monotonicity.append(correlation)
        result[factor] = {
            "months": len(dates),
            "mean_q5_minus_q1": _mean_or_none(spreads),
            "annualized_q5_minus_q1": (
                _mean_or_none(spreads) * 12 if spreads else None
            ),
            "positive_spread_rate": (
                sum(value > 0 for value in spreads) / len(spreads) if spreads else None
            ),
            "mean_monotonicity": _mean_or_none(monotonicity),
        }
    return result


def _panel_statistics(
    path: Path,
) -> tuple[
    dict[str, float | None],
    list[dict[str, object]],
    dict[tuple[str, str], dict[str, float | int]],
]:
    previous: dict[str, set[str]] = {}
    turnover_values: dict[str, list[float]] = defaultdict(list)
    turnover_rows: list[dict[str, object]] = []
    correlation_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(INVESTABLE_COLUMNS):
            raise ValueError("investable factor columns are not canonical")
        current_date = ""
        rows: list[dict[str, str]] = []
        for row in reader:
            if current_date and row["date"] != current_date:
                _analyze_date(
                    current_date,
                    rows,
                    previous,
                    turnover_values,
                    turnover_rows,
                    correlation_values,
                )
                rows = []
            current_date = row["date"]
            rows.append(row)
        if rows:
            _analyze_date(
                current_date,
                rows,
                previous,
                turnover_values,
                turnover_rows,
                correlation_values,
            )
    turnover_summary = {
        factor: _mean_or_none(values) for factor, values in turnover_values.items()
    }
    correlations = {
        pair: {"months": len(values), "mean_correlation": statistics.fmean(values)}
        for pair, values in correlation_values.items()
    }
    return turnover_summary, turnover_rows, correlations


def _analyze_date(
    date: str,
    rows: list[dict[str, str]],
    previous: dict[str, set[str]],
    turnover_values: dict[str, list[float]],
    turnover_rows: list[dict[str, object]],
    correlation_values: dict[tuple[str, str], list[float]],
) -> None:
    for factor in FACTOR_NAMES:
        members = {row["symbol"] for row in rows if row[f"{factor}_quantile"] == "5"}
        if factor in previous and previous[factor]:
            retained = len(members & previous[factor]) / len(previous[factor])
            turnover = 1 - retained
            turnover_values[factor].append(turnover)
            turnover_rows.append(
                {
                    "date": date,
                    "factor": factor,
                    "top_quantile_turnover": _number(turnover),
                }
            )
        previous[factor] = members
    for first, second in combinations(FACTOR_NAMES, 2):
        correlation = pearson_correlation(
            [_optional(row[f"{first}_rank"]) for row in rows],
            [_optional(row[f"{second}_rank"]) for row in rows],
        )
        if correlation is not None:
            correlation_values[(first, second)].append(correlation)


def _series_summary(values: list[float]) -> dict[str, float | int | None]:
    mean = statistics.fmean(values)
    standard_deviation = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "months": len(values),
        "mean": mean,
        "standard_deviation": standard_deviation,
        "information_ratio": (
            mean / standard_deviation if standard_deviation else None
        ),
        "t_statistic": (
            mean / (standard_deviation / math.sqrt(len(values)))
            if standard_deviation
            else None
        ),
        "positive_rate": sum(value > 0 for value in values) / len(values),
    }


def _write_json_atomic(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)


def _write_csv_atomic(
    path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]
) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _optional(value: str) -> float | None:
    return float(value) if value else None


def _mean_or_none(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _number(value: float | None) -> str:
    return "" if value is None else format(value, ".15g")
