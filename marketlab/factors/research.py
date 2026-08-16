"""Monthly point-in-time factor panel and diagnostics."""

import csv
import gzip
import json
import math
import tempfile
from collections import defaultdict
from contextlib import ExitStack
from pathlib import Path

from marketlab.factors.information_coefficient import spearman_ic
from marketlab.factors.quantiles import quantile_mean_returns
from marketlab.factors.ranking import percentile_ranks, quantile
from marketlab.features.fundamental.ratios import FUNDAMENTAL_FEATURE_COLUMNS
from marketlab.features.technical.daily import TECHNICAL_COLUMNS

FACTOR_NAMES = (
    "momentum_12_1",
    "volatility_63",
    "book_to_market",
    "earnings_yield",
    "gross_profitability",
    "asset_growth_yoy",
)
STAGING_COLUMNS = ("date", "symbol", "forward_return_21", *FACTOR_NAMES)
PANEL_COLUMNS = (
    "date",
    "symbol",
    "forward_return_21",
    *FACTOR_NAMES,
    *(f"{name}_rank" for name in FACTOR_NAMES),
    *(f"{name}_quantile" for name in FACTOR_NAMES),
)


def build_monthly_factor_research(
    technical: Path,
    fundamental: Path,
    panel: Path,
    ic_output: Path,
    quantile_output: Path,
) -> dict[str, int]:
    """Build a monthly factor panel and cross-sectional diagnostics."""

    for path in (panel, ic_output, quantile_output):
        if path.exists():
            raise FileExistsError(f"factor output already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    fundamentals = _load_fundamentals(fundamental)
    panel_partial = panel.with_name(f"{panel.name}.part")
    ic_partial = ic_output.with_name(f"{ic_output.name}.part")
    quantile_partial = quantile_output.with_name(f"{quantile_output.name}.part")
    observations = 0
    ic_rows = 0
    quantile_rows = 0
    try:
        with tempfile.TemporaryDirectory(prefix="marketlab-factor-") as temp_name:
            rebalance_dates = _benchmark_month_ends(technical)
            years = _stage_month_ends(
                technical, fundamentals, rebalance_dates, Path(temp_name)
            )
            with (
                gzip.open(
                    panel_partial, "wt", encoding="utf-8", newline=""
                ) as panel_file,
                ic_partial.open("w", encoding="utf-8", newline="") as ic_file,
                quantile_partial.open(
                    "w", encoding="utf-8", newline=""
                ) as quantile_file,
            ):
                panel_writer = csv.DictWriter(panel_file, fieldnames=PANEL_COLUMNS)
                ic_writer = csv.DictWriter(
                    ic_file, fieldnames=("date", "factor", "observations", "ic")
                )
                quantile_writer = csv.DictWriter(
                    quantile_file,
                    fieldnames=("date", "factor", "quantile", "mean_forward_return"),
                )
                panel_writer.writeheader()
                ic_writer.writeheader()
                quantile_writer.writeheader()
                for year in sorted(years):
                    dates: dict[str, list[dict[str, str]]] = defaultdict(list)
                    with years[year].open(encoding="utf-8", newline="") as file:
                        for row in csv.DictReader(file):
                            dates[row["date"]].append(row)
                    for date_text in sorted(dates):
                        counts = _rank_date(
                            dates[date_text], panel_writer, ic_writer, quantile_writer
                        )
                        observations += counts[0]
                        ic_rows += counts[1]
                        quantile_rows += counts[2]
        panel_partial.replace(panel)
        ic_partial.replace(ic_output)
        quantile_partial.replace(quantile_output)
    except BaseException:
        for path in (panel_partial, ic_partial, quantile_partial):
            path.unlink(missing_ok=True)
        raise
    result = {
        "observations": observations,
        "ic_rows": ic_rows,
        "quantile_rows": quantile_rows,
    }
    panel.with_suffix(panel.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _load_fundamentals(path: Path) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(FUNDAMENTAL_FEATURE_COLUMNS):
            raise ValueError("fundamental feature columns are not canonical")
        for row in reader:
            result[row["symbol"]].append(row)
    for rows in result.values():
        rows.sort(key=lambda row: row["available_date"])
    return dict(result)


def _stage_month_ends(
    technical: Path,
    fundamentals: dict[str, list[dict[str, str]]],
    rebalance_dates: set[str],
    temp_root: Path,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    with ExitStack() as stack:
        writers: dict[str, csv.DictWriter] = {}
        with gzip.open(technical, "rt", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != list(TECHNICAL_COLUMNS):
                raise ValueError("technical feature columns are not canonical")
            current_symbol = ""
            rows: list[dict[str, str]] = []
            for row in reader:
                if current_symbol and row["symbol"] != current_symbol:
                    _stage_symbol(
                        rows,
                        fundamentals.get(current_symbol, []),
                        rebalance_dates,
                        paths,
                        writers,
                        stack,
                        temp_root,
                    )
                    rows = []
                current_symbol = row["symbol"]
                rows.append(row)
            if rows:
                _stage_symbol(
                    rows,
                    fundamentals.get(current_symbol, []),
                    rebalance_dates,
                    paths,
                    writers,
                    stack,
                    temp_root,
                )
    return paths


def _stage_symbol(
    rows: list[dict[str, str]],
    fundamentals: list[dict[str, str]],
    rebalance_dates: set[str],
    paths: dict[str, Path],
    writers: dict[str, csv.DictWriter],
    stack: ExitStack,
    temp_root: Path,
) -> None:
    fundamental_index = 0
    latest: dict[str, str] = {}
    for index, row in enumerate(rows):
        if row["date"] not in rebalance_dates or index + 21 >= len(rows):
            continue
        while (
            fundamental_index < len(fundamentals)
            and fundamentals[fundamental_index]["available_date"][:10] < row["date"]
        ):
            latest = fundamentals[fundamental_index]
            fundamental_index += 1
        forward = 1.0
        valid_forward = True
        for future in rows[index + 1 : index + 22]:
            if not future["return_1d"]:
                valid_forward = False
                break
            forward *= 1 + float(future["return_1d"])
        staged = {
            "date": row["date"],
            "symbol": row["symbol"],
            "forward_return_21": format(forward - 1, ".15g") if valid_forward else "",
        }
        for factor in FACTOR_NAMES:
            staged[factor] = row.get(factor, "") or latest.get(factor, "")
        year = row["date"][:4]
        if year not in writers:
            path = temp_root / f"{year}.csv"
            handle = stack.enter_context(path.open("w", encoding="utf-8", newline=""))
            writer = csv.DictWriter(handle, fieldnames=STAGING_COLUMNS)
            writer.writeheader()
            writers[year] = writer
            paths[year] = path
        writers[year].writerow(staged)


def _benchmark_month_ends(technical: Path, benchmark: str = "SPY") -> set[str]:
    month_ends: dict[str, str] = {}
    with gzip.open(technical, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(TECHNICAL_COLUMNS):
            raise ValueError("technical feature columns are not canonical")
        for row in reader:
            if row["symbol"] == benchmark:
                month_ends[row["date"][:7]] = row["date"]
    if not month_ends:
        raise ValueError(f"benchmark {benchmark} is absent from technical features")
    return set(month_ends.values())


def _rank_date(
    rows: list[dict[str, str]],
    panel_writer: csv.DictWriter,
    ic_writer: csv.DictWriter,
    quantile_writer: csv.DictWriter,
) -> tuple[int, int, int]:
    forward = [_float(row["forward_return_21"]) for row in rows]
    ranks: dict[str, list[float | None]] = {}
    quantiles: dict[str, list[int | None]] = {}
    ic_count = 0
    quantile_count = 0
    for factor in FACTOR_NAMES:
        values = [_float(row[factor]) for row in rows]
        factor_ranks = percentile_ranks(values)
        factor_quantiles = [quantile(rank) for rank in factor_ranks]
        ranks[factor] = factor_ranks
        quantiles[factor] = factor_quantiles
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
        for bucket, mean_return in quantile_mean_returns(
            factor_quantiles, forward
        ).items():
            quantile_writer.writerow(
                {
                    "date": rows[0]["date"],
                    "factor": factor,
                    "quantile": bucket,
                    "mean_forward_return": _number(mean_return),
                }
            )
            quantile_count += 1
    for index, row in enumerate(rows):
        output = {column: row.get(column, "") for column in STAGING_COLUMNS}
        for factor in FACTOR_NAMES:
            output[f"{factor}_rank"] = _number(ranks[factor][index])
            output[f"{factor}_quantile"] = quantiles[factor][index] or ""
        panel_writer.writerow(output)
    return len(rows), ic_count, quantile_count


def _float(value: str) -> float | None:
    if not value:
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _number(value: float | None) -> str:
    return "" if value is None else format(value, ".15g")
