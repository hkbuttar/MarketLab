"""Portfolio sector, factor, and concentration exposure analysis."""

import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

FACTOR_RANKS = (
    "momentum_12_1_rank",
    "volatility_63_rank",
    "book_to_market_rank",
    "earnings_yield_rank",
    "gross_profitability_rank",
    "asset_growth_yoy_rank",
)


def build_exposure_report(
    targets_path: Path,
    panel_path: Path,
    overview_root: Path,
    regression_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Build current-label sector and cross-sectional factor exposures."""

    sectors = load_current_sectors(overview_root)
    benchmark = _benchmark_sector_proxy(panel_path, sectors)
    sector_rows, concentration, strategies = _portfolio_sector_exposures(
        targets_path, sectors, benchmark
    )
    factor_rows = [
        row
        for strategy in strategies
        for row in _strategy_factor_exposures(targets_path, panel_path, strategy)
    ]
    regression = json.loads(regression_path.read_text(encoding="utf-8"))
    summary: dict[str, object] = {
        "classification_source": "Alpha Vantage current OVERVIEW labels",
        "historical_classification_warning": (
            "Sector labels have no effective dates and are not point-in-time GICS. "
            "Benchmark sector weights are an ADV-weighted investable-universe proxy."
        ),
        "classified_symbols": len(sectors),
        "strategies": {},
    }
    for strategy in strategies:
        values = concentration[strategy]
        regression_values = regression.get(strategy, {})
        summary["strategies"][strategy] = {
            "average_hhi": _mean([row["hhi"] for row in values]),
            "average_effective_holdings": _mean(
                [row["effective_holdings"] for row in values]
            ),
            "average_top_10_weight": _mean([row["top_10_weight"] for row in values]),
            "market_beta": regression_values.get("coefficients", {}).get("market"),
            "latest_sector_weights": {
                row["sector"]: row["portfolio_weight"]
                for row in sector_rows
                if row["strategy"] == strategy
                and row["date"]
                == max(
                    item["date"] for item in sector_rows if item["strategy"] == strategy
                )
            },
        }
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_directory / "sector_exposures.csv",
        sector_rows,
        (
            "date",
            "strategy",
            "sector",
            "portfolio_weight",
            "benchmark_proxy_weight",
            "active_weight",
        ),
    )
    _write_csv(
        output_directory / "factor_exposures.csv",
        factor_rows,
        ("date", "strategy", *FACTOR_RANKS, "coverage_weight"),
    )
    _write_json(output_directory / "exposure_summary.json", summary)
    return summary


def load_current_sectors(root: Path) -> dict[str, str]:
    """Load latest available Alpha Vantage sector label for each symbol."""

    result: dict[str, str] = {}
    for path in root.glob("*_overview/*/*_overview.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        symbol = str(payload.get("Symbol", "")).strip().upper()
        sector = str(payload.get("Sector", "")).strip().upper()
        if symbol and sector and sector not in {"NONE", "N/A"}:
            result[symbol] = sector
    return result


def _portfolio_sector_exposures(
    targets_path: Path,
    sectors: dict[str, str],
    benchmark: dict[str, dict[str, float]],
) -> tuple[list[dict[str, object]], dict[str, list[dict[str, float]]], list[str]]:
    weights: dict[tuple[str, str, str], float] = defaultdict(float)
    positions: dict[tuple[str, str], list[float]] = defaultdict(list)
    with gzip.open(targets_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            weight = float(row["weight"])
            sector = sectors.get(row["symbol"], "UNCLASSIFIED")
            weights[(row["date"], row["strategy"], sector)] += weight
            positions[(row["date"], row["strategy"])].append(weight)
    rows: list[dict[str, object]] = []
    for (date, strategy, sector), weight in sorted(weights.items()):
        reference = benchmark.get(date, {}).get(sector, 0.0)
        rows.append(
            {
                "date": date,
                "strategy": strategy,
                "sector": sector,
                "portfolio_weight": weight,
                "benchmark_proxy_weight": reference,
                "active_weight": weight - reference,
            }
        )
    concentration: dict[str, list[dict[str, float]]] = defaultdict(list)
    for (_, strategy), values in positions.items():
        hhi = sum(weight**2 for weight in values)
        concentration[strategy].append(
            {
                "hhi": hhi,
                "effective_holdings": 1.0 / hhi if hhi else 0.0,
                "top_10_weight": sum(sorted(values, reverse=True)[:10]),
            }
        )
    return rows, dict(concentration), sorted(concentration)


def _benchmark_sector_proxy(
    panel_path: Path, sectors: dict[str, str]
) -> dict[str, dict[str, float]]:
    values: dict[tuple[str, str], float] = defaultdict(float)
    totals: dict[str, float] = defaultdict(float)
    with gzip.open(panel_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if not row["average_dollar_volume_21"]:
                continue
            value = float(row["average_dollar_volume_21"])
            sector = sectors.get(row["symbol"], "UNCLASSIFIED")
            values[(row["date"], sector)] += value
            totals[row["date"]] += value
    result: dict[str, dict[str, float]] = defaultdict(dict)
    for (date, sector), value in values.items():
        result[date][sector] = value / totals[date] if totals[date] else 0.0
    return dict(result)


def _strategy_factor_exposures(
    targets_path: Path, panel_path: Path, strategy: str
) -> list[dict[str, object]]:
    targets: dict[tuple[str, str], float] = {}
    with gzip.open(targets_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["strategy"] == strategy:
                targets[(row["date"], row["symbol"])] = float(row["weight"])
    sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    coverage: dict[str, float] = defaultdict(float)
    with gzip.open(panel_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            weight = targets.get((row["date"], row["symbol"]))
            if weight is None:
                continue
            available = [column for column in FACTOR_RANKS if row[column]]
            if available:
                coverage[row["date"]] += weight
            for column in available:
                sums[row["date"]][column] += weight * (float(row[column]) - 0.5) * 2.0
    return [
        {
            "date": date,
            "strategy": strategy,
            **{column: values.get(column, 0.0) for column in FACTOR_RANKS},
            "coverage_weight": coverage[date],
        }
        for date, values in sorted(sums.items())
    ]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def _write_csv(
    path: Path, rows: list[dict[str, object]], columns: tuple[str, ...]
) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
