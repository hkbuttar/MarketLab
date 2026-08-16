"""Transparent internal MarketLab robustness diagnostic."""

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import annualized_return

WEIGHTS = {
    "out_of_sample_performance": 0.30,
    "cost_resilience": 0.20,
    "parameter_stability": 0.20,
    "regime_stability": 0.15,
    "bootstrap_confidence": 0.15,
}


def build_robustness_scores(
    results_path: Path,
    costs_path: Path,
    sensitivity_path: Path,
    regimes_path: Path,
    bootstrap_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Combine five separately visible robustness components into a score."""

    components: dict[str, dict[str, float]] = defaultdict(dict)
    _out_of_sample_scores(results_path, components)
    _cost_scores(costs_path, components)
    _parameter_scores(sensitivity_path, components)
    _regime_scores(regimes_path, components)
    _bootstrap_scores(bootstrap_path, components)
    strategies: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    for strategy, values in sorted(components.items()):
        missing = sorted(set(WEIGHTS) - set(values))
        if missing:
            raise ValueError(f"{strategy} is missing score components: {missing}")
        overall = sum(values[name] * weight for name, weight in WEIGHTS.items())
        result = {**values, "overall_score": overall, "label": _score_label(overall)}
        strategies[strategy] = result
        rows.append({"strategy": strategy, **result})
    report: dict[str, object] = {
        "name": "MarketLab robustness diagnostic",
        "industry_standard": False,
        "weights": WEIGHTS,
        "methodology": {
            "out_of_sample_performance": (
                "Chronological final-20% holdout; average of absolute and SPY-relative "
                "CAGR scores, each scaled from -10% to +10%."
            ),
            "cost_resilience": "Highest attractive tested bps divided by 50 bps.",
            "parameter_stability": (
                "Equal blend of positive-return variant share and Sharpe consistency; "
                "multi-factor uses the union of tested momentum and volatility grids."
            ),
            "regime_stability": (
                "Equal blend of positive-CAGR regime share and conditional "
                "hit-rate score."
            ),
            "bootstrap_confidence": ("Average of P(Sharpe > 0) and P(CAGR > SPY)."),
        },
        "strategies": strategies,
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_json(output_directory / "robustness_scores.json", report)
    _write_csv(output_directory / "robustness_scores.csv", rows)
    return report


def _out_of_sample_scores(path: Path, components: dict[str, dict[str, float]]) -> None:
    series: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series[row["strategy"]].append(row)
    for strategy, rows in series.items():
        start = math.floor(len(rows) * 0.80)
        holdout = rows[start:]
        returns = [float(row["daily_return"]) for row in holdout]
        benchmark_nav = [float(row["benchmark_nav"]) for row in holdout]
        benchmark_returns = [0.0] + [
            current / previous - 1.0
            for previous, current in zip(benchmark_nav, benchmark_nav[1:], strict=False)
        ]
        cagr = annualized_return(returns)
        benchmark_cagr = annualized_return(benchmark_returns)
        absolute = _scaled(cagr, -0.10, 0.10)
        relative = _scaled(cagr - benchmark_cagr, -0.10, 0.10)
        components[strategy]["out_of_sample_performance"] = (absolute + relative) / 2


def _cost_scores(path: Path, components: dict[str, dict[str, float]]) -> None:
    attractive: dict[str, list[int]] = defaultdict(list)
    strategies: set[str] = set()
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            strategy = row["strategy"]
            strategies.add(strategy)
            if row["economically_attractive"] == "True":
                attractive[strategy].append(int(row["cost_bps"]))
    for strategy in strategies:
        highest = max(attractive[strategy], default=0)
        components[strategy]["cost_resilience"] = min(100.0, highest / 50 * 100)


def _parameter_scores(path: Path, components: dict[str, dict[str, float]]) -> None:
    families: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            families[row["factor_family"]].append(row)
    mapping = {
        "momentum": families["momentum"],
        "low_volatility": families["volatility"],
        "quality_value_momentum": [*families["momentum"], *families["volatility"]],
    }
    for strategy, rows in mapping.items():
        returns = [float(row["annualized_return"]) for row in rows]
        sharpes = [float(row["sharpe"]) for row in rows]
        positive = sum(value > 0 for value in returns) / len(returns) * 100
        mean = statistics.mean(sharpes)
        dispersion = statistics.pstdev(sharpes)
        consistency = max(0.0, 100.0 * (1.0 - dispersion / max(abs(mean), 1e-12)))
        components[strategy]["parameter_stability"] = (positive + consistency) / 2


def _regime_scores(path: Path, components: dict[str, dict[str, float]]) -> None:
    values: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            values[row["strategy"]].append(row)
    for strategy, rows in values.items():
        positive = sum(float(row["cagr"]) > 0 for row in rows) / len(rows) * 100
        hit_rate = statistics.mean(float(row["hit_rate"]) for row in rows)
        hit_score = _scaled(hit_rate, 0.45, 0.55)
        components[strategy]["regime_stability"] = (positive + hit_score) / 2


def _bootstrap_scores(path: Path, components: dict[str, dict[str, float]]) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    for strategy, values in report["strategies"].items():
        score = (
            values["probability_sharpe_positive"]
            + values["probability_cagr_above_benchmark"]
        ) / 2
        components[strategy]["bootstrap_confidence"] = score * 100


def _scaled(value: float, lower: float, upper: float) -> float:
    return max(0.0, min(100.0, (value - lower) / (upper - lower) * 100))


def _score_label(value: float) -> str:
    if value >= 75:
        return "strong"
    if value >= 60:
        return "moderate"
    if value >= 40:
        return "mixed"
    return "weak"


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = ("strategy", *WEIGHTS, "overall_score", "label")
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)
