"""Read persisted factor research without recalculating factor definitions."""

import csv
import gzip
import json
import statistics
from collections import Counter
from functools import lru_cache
from pathlib import Path

from backend.schemas.factor_lab import DatedValue, FactorLabResult, NamedValue
from marketlab.factors.research import FACTOR_NAMES

FACTOR_ROOT = Path("reports/factors")
PANEL_PATH = Path("data/features/factors/monthly_panel_investable.csv.gz")
OVERVIEW_ROOT = Path("data/raw/fundamentals/alpha_vantage")
SECTOR_NOTE = (
    "Sector composition uses current Alpha Vantage labels because historically "
    "effective GICS classifications are not available."
)


def available_factors(root: Path = FACTOR_ROOT) -> list[str]:
    """Return registered factors independently of local generated artifacts."""

    del root
    return sorted(FACTOR_NAMES)


def factor_lab_result(
    factor: str,
    start_date: str,
    end_date: str,
    *,
    root: Path = FACTOR_ROOT,
    panel_path: Path = PANEL_PATH,
    overview_root: Path = OVERVIEW_ROOT,
) -> FactorLabResult:
    """Aggregate one factor over an explicit date window."""

    factors = available_factors(root)
    if factor not in factors:
        raise KeyError(factor)
    if end_date < start_date:
        raise ValueError("end_date must not precede start_date")
    ic_rows = _dated_rows(
        root / "information_coefficients_investable.csv",
        factor,
        start_date,
        end_date,
        "ic",
    )
    if not ic_rows:
        raise ValueError("no factor observations match the requested date range")
    ic_values = [value for _, value in ic_rows]
    turnover = _dated_rows(
        root / "top_quantile_turnover.csv",
        factor,
        start_date,
        end_date,
        "top_quantile_turnover",
    )
    return FactorLabResult(
        factor=factor,
        universe="investable_us_equities",
        forward_horizon=21,
        start_date=ic_rows[0][0],
        end_date=ic_rows[-1][0],
        observations=len(ic_values),
        mean_ic=statistics.fmean(ic_values),
        positive_ic_rate=sum(value > 0 for value in ic_values) / len(ic_values),
        mean_turnover=(
            statistics.fmean(value for _, value in turnover) if turnover else None
        ),
        ic_history=[DatedValue(date=date, value=value) for date, value in ic_rows],
        quantile_returns=_quantiles(root, factor, start_date, end_date),
        correlations=_correlations(root, factor),
        sector_exposure=_sector_exposure(
            factor, start_date, end_date, panel_path, overview_root
        ),
        sector_classification_note=SECTOR_NOTE,
    )


def _dated_rows(
    path: Path, factor: str, start: str, end: str, value_column: str
) -> list[tuple[str, float]]:
    values: list[tuple[str, float]] = []
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if (
                row["factor"] == factor
                and start <= row["date"] <= end
                and row[value_column]
            ):
                values.append((row["date"], float(row[value_column])))
    return values


def _quantiles(root: Path, factor: str, start: str, end: str) -> list[NamedValue]:
    values: dict[str, list[float]] = {}
    path = root / "quantile_returns_investable.csv"
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["factor"] == factor and start <= row["date"] <= end:
                values.setdefault(row["quantile"], []).append(
                    float(row["mean_forward_return"])
                )
    return [
        NamedValue(name=f"Q{quantile}", value=statistics.fmean(observations))
        for quantile, observations in sorted(
            values.items(), key=lambda item: int(item[0])
        )
    ]


def _correlations(root: Path, factor: str) -> list[NamedValue]:
    output: list[NamedValue] = []
    with (root / "factor_correlations.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["factor_a"] == factor:
                output.append(
                    NamedValue(
                        name=row["factor_b"], value=float(row["mean_correlation"])
                    )
                )
            elif row["factor_b"] == factor:
                output.append(
                    NamedValue(
                        name=row["factor_a"], value=float(row["mean_correlation"])
                    )
                )
    return sorted(output, key=lambda item: abs(item.value), reverse=True)


@lru_cache(maxsize=32)
def _sector_exposure_cached(
    factor: str, start: str, end: str, panel: str, overviews: str
) -> tuple[tuple[str, float], ...]:
    sectors = _current_sectors(Path(overviews))
    counts: Counter[str] = Counter()
    total = 0
    quantile_column = f"{factor}_quantile"
    with gzip.open(panel, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if start <= row["date"] <= end and row.get(quantile_column) == "5":
                sector = sectors.get(row["symbol"], "Unknown")
                counts[sector] += 1
                total += 1
    if not total:
        return ()
    return tuple((sector, count / total) for sector, count in counts.most_common())


def _sector_exposure(
    factor: str, start: str, end: str, panel: Path, overviews: Path
) -> list[NamedValue]:
    return [
        NamedValue(name=name, value=value)
        for name, value in _sector_exposure_cached(
            factor, start, end, str(panel.resolve()), str(overviews.resolve())
        )
    ]


def _current_sectors(root: Path) -> dict[str, str]:
    sectors: dict[str, str] = {}
    for path in root.glob("*_overview/*/*_overview.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        symbol = str(value.get("Symbol", ""))
        sector = str(value.get("Sector", "")).strip()
        if symbol and sector:
            sectors[symbol] = sector
    return sectors
