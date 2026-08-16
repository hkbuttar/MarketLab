"""Seeded moving-block bootstrap robustness analysis."""

import csv
import gzip
import json
import random
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import annualized_return, sharpe_ratio, sortino_ratio

BOOTSTRAP_METRICS = ("cagr", "sharpe", "sortino", "maximum_drawdown")


def run_bootstrap_analysis(
    results_path: Path,
    factors_path: Path,
    output_directory: Path,
    *,
    iterations: int = 1_000,
    block_size: int = 21,
    seed: int = 1729,
) -> dict[str, object]:
    """Bootstrap paired strategy/benchmark returns and save uncertainty results."""

    risk_free: dict[str, float] = {}
    with gzip.open(factors_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            risk_free[row["date"]] = float(row["risk_free"])
    series: dict[str, list[dict[str, str]]] = defaultdict(list)
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series[row["strategy"]].append(row)
    rng = random.Random(seed)
    report: dict[str, object] = {
        "method": "paired moving-block bootstrap",
        "iterations": iterations,
        "block_size": block_size,
        "seed": seed,
        "strategies": {},
    }
    sample_rows: list[dict[str, object]] = []
    for strategy, rows in sorted(series.items()):
        strategy_returns = [float(row["daily_return"]) for row in rows]
        benchmark_nav = [float(row["benchmark_nav"]) for row in rows]
        benchmark_returns = [0.0] + [
            current / previous - 1.0
            for previous, current in zip(benchmark_nav, benchmark_nav[1:], strict=False)
        ]
        daily_risk_free = [risk_free.get(row["date"], 0.0) for row in rows]
        samples = bootstrap_series(
            strategy_returns,
            benchmark_returns,
            daily_risk_free,
            iterations=iterations,
            block_size=block_size,
            rng=rng,
        )
        for index, sample in enumerate(samples):
            sample_rows.append({"strategy": strategy, "iteration": index, **sample})
        report["strategies"][strategy] = _summarize(samples)
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_json(output_directory / "bootstrap_summary.json", report)
    _write_samples(output_directory / "bootstrap_samples.csv.gz", sample_rows)
    return report


def bootstrap_series(
    strategy_returns: list[float],
    benchmark_returns: list[float],
    daily_risk_free: list[float],
    *,
    iterations: int,
    block_size: int,
    rng: random.Random,
) -> list[dict[str, float]]:
    """Return paired moving-block bootstrap metric samples."""

    length = len(strategy_returns)
    if length != len(benchmark_returns) or length != len(daily_risk_free):
        raise ValueError("bootstrap series must be aligned")
    if length < 2 or not 1 <= block_size <= length:
        raise ValueError("invalid bootstrap block size")
    starts = range(length - block_size + 1)
    result: list[dict[str, float]] = []
    for _ in range(iterations):
        indices: list[int] = []
        while len(indices) < length:
            start = rng.choice(starts)
            indices.extend(range(start, start + block_size))
        indices = indices[:length]
        strategy = [strategy_returns[index] for index in indices]
        benchmark = [benchmark_returns[index] for index in indices]
        risk_free = [daily_risk_free[index] for index in indices]
        annual_risk_free = (1.0 + sum(risk_free) / len(risk_free)) ** 252 - 1.0
        result.append(
            {
                "cagr": annualized_return(strategy),
                "benchmark_cagr": annualized_return(benchmark),
                "sharpe": sharpe_ratio(strategy, annual_risk_free),
                "sortino": sortino_ratio(strategy, annual_risk_free),
                "maximum_drawdown": _maximum_drawdown(strategy),
            }
        )
    return result


def _summarize(samples: list[dict[str, float]]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for metric in BOOTSTRAP_METRICS:
        values = sorted(sample[metric] for sample in samples)
        summary[metric] = {
            "lower_95": _percentile(values, 0.025),
            "median": _percentile(values, 0.50),
            "upper_95": _percentile(values, 0.975),
        }
    summary["probability_sharpe_positive"] = sum(
        sample["sharpe"] > 0 for sample in samples
    ) / len(samples)
    summary["probability_cagr_above_benchmark"] = sum(
        sample["cagr"] > sample["benchmark_cagr"] for sample in samples
    ) / len(samples)
    return summary


def _maximum_drawdown(returns: list[float]) -> float:
    wealth = 1.0
    peak = 1.0
    maximum = 0.0
    for value in returns:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        maximum = min(maximum, wealth / peak - 1.0)
    return maximum


def _percentile(values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)


def _write_samples(path: Path, rows: list[dict[str, object]]) -> None:
    columns = (
        "strategy",
        "iteration",
        "cagr",
        "benchmark_cagr",
        "sharpe",
        "sortino",
        "maximum_drawdown",
    )
    partial = path.with_name(f"{path.name}.part")
    with gzip.open(partial, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)
