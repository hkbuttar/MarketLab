"""Representative pipeline benchmarks using production entry points."""

from __future__ import annotations

import csv
import gzip
import resource
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from marketlab.backtest import run_daily_backtest
from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.features.technical import build_daily_technical_features
from marketlab.ml.training import run_walk_forward_training
from marketlab.validation.bootstrap import run_bootstrap_analysis
from marketlab.validation.sensitivity import run_parameter_sensitivity

DEFAULT_WORKLOADS = (
    "data_load",
    "feature_generation",
    "backtest_10y",
    "bootstrap_250",
)
EXPENSIVE_WORKLOADS = ("walk_forward_ml", "parameter_grid")


@dataclass(frozen=True)
class BenchmarkResult:
    """One independently measured workload."""

    workload: str
    elapsed_seconds: float
    peak_rss_mb: float
    details: dict[str, object]


def peak_rss_mb(maximum_rss: int | float | None = None) -> float:
    """Normalize ``ru_maxrss`` to MiB on macOS and Linux."""

    value = (
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if maximum_rss is None
        else maximum_rss
    )
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return float(value) / divisor


def run_workload(name: str, root: Path) -> BenchmarkResult:
    """Run and measure one workload in the current process."""

    workloads: dict[str, Callable[[Path], dict[str, object]]] = {
        "data_load": _data_load,
        "feature_generation": _feature_generation,
        "backtest_10y": _backtest_10y,
        "bootstrap_250": _bootstrap,
        "walk_forward_ml": _walk_forward_ml,
        "parameter_grid": _parameter_grid,
    }
    try:
        workload = workloads[name]
    except KeyError as error:
        raise ValueError(f"unknown benchmark workload: {name}") from error
    started = time.perf_counter()
    details = workload(root)
    return BenchmarkResult(
        workload=name,
        elapsed_seconds=time.perf_counter() - started,
        peak_rss_mb=peak_rss_mb(),
        details=details,
    )


def result_dict(result: BenchmarkResult) -> dict[str, object]:
    """Return a JSON-compatible benchmark result."""

    return asdict(result)


def _data_load(root: Path) -> dict[str, object]:
    source = root / "data/features/factors/monthly_panel_investable.csv.gz"
    rows = 0
    symbols: set[str] = set()
    with gzip.open(source, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            rows += 1
            symbols.add(row["symbol"])
    return {"rows": rows, "symbols": len(symbols), "source": str(source)}


def _feature_generation(root: Path) -> dict[str, object]:
    source = root / "data/processed/prices/prices_clean.csv.gz"
    with tempfile.TemporaryDirectory(prefix="marketlab-benchmark-") as directory:
        temporary = Path(directory)
        sample = temporary / "prices_25_symbols.csv.gz"
        symbols = _copy_symbol_sample(source, sample, limit=25)
        result = build_daily_technical_features(sample, temporary / "technical.csv.gz")
    return {**result, "sample_symbols": symbols, "source": str(source)}


def _copy_symbol_sample(source: Path, destination: Path, *, limit: int) -> int:
    selected: set[str] = set()
    with (
        gzip.open(source, "rt", encoding="utf-8", newline="") as input_file,
        gzip.open(destination, "wt", encoding="utf-8", newline="") as output_file,
    ):
        reader = csv.DictReader(input_file)
        if reader.fieldnames != list(PRICE_COLUMNS):
            raise ValueError("price columns do not match the canonical schema")
        writer = csv.DictWriter(output_file, fieldnames=PRICE_COLUMNS)
        writer.writeheader()
        for row in reader:
            if row["symbol"] not in selected:
                if len(selected) == limit:
                    break
                selected.add(row["symbol"])
            writer.writerow(row)
    return len(selected)


def _backtest_10y(root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="marketlab-benchmark-") as directory:
        summary = run_daily_backtest(
            root / "data/features/portfolios/monthly_targets.csv.gz",
            root / "data/processed/prices/prices_clean.csv.gz",
            root / "data/features/portfolios/rebalance_trades_split_adjusted.csv.gz",
            root / "data/processed/reference/security_crosswalk.csv.gz",
            Path(directory) / "daily_results.csv",
            strategies={"momentum"},
            start_date="2016-01-01",
            end_date="2025-12-31",
        )
    return {"strategies": list(summary), "start": "2016-01-01", "end": "2025-12-31"}


def _bootstrap(root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="marketlab-benchmark-") as directory:
        report = run_bootstrap_analysis(
            root / "data/features/backtests/daily_results.csv",
            root / "data/raw/factors/french_daily.csv.gz",
            Path(directory),
            iterations=250,
        )
    return {"iterations": 250, "strategies": list(report["strategies"])}


def _walk_forward_ml(root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="marketlab-benchmark-") as directory:
        metadata = run_walk_forward_training(
            root / "data/features/ml/cross_sectional_ranking.csv.gz",
            Path(directory) / "predictions.csv.gz",
            model_names=("elastic_net",),
            first_test_year=2025,
            purge_calendar_path=root / "data/features/regimes/daily_regimes.csv",
        )
    return {
        "models": metadata["models"],
        "folds": len(metadata["folds"]),
        "prediction_rows": metadata["prediction_rows"],
    }


def _parameter_grid(root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="marketlab-benchmark-") as directory:
        rows = run_parameter_sensitivity(
            root / "data/processed/prices/prices_clean.csv.gz", Path(directory)
        )
    return {"configurations": len(rows)}
