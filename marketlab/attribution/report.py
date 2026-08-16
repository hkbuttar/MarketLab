"""Factor-attribution report orchestration."""

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

from marketlab.attribution.factor_regression import ols_factor_regression

FACTOR_NAMES = [
    "market",
    "size",
    "value",
    "profitability",
    "investment",
    "momentum",
]
FACTOR_COLUMNS = [
    "market_excess",
    "size",
    "value",
    "profitability",
    "investment",
    "momentum",
]


def build_factor_attribution(
    results_path: Path, factors_path: Path, output_path: Path
) -> dict[str, object]:
    """Align strategy returns to French factors and save regression diagnostics."""

    factors: dict[str, dict[str, float]] = {}
    with gzip.open(factors_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            factors[row["date"]] = {
                key: float(value) for key, value in row.items() if key != "date"
            }
    strategies: dict[str, list[dict[str, str]]] = defaultdict(list)
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["date"] in factors:
                strategies[row["strategy"]].append(row)
    report: dict[str, object] = {}
    for strategy, rows in sorted(strategies.items()):
        excess_returns = [
            float(row["daily_return"]) - factors[row["date"]]["risk_free"]
            for row in rows
        ]
        observations = [
            [factors[row["date"]][column] for column in FACTOR_COLUMNS] for row in rows
        ]
        report[strategy] = ols_factor_regression(
            excess_returns, observations, FACTOR_NAMES
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(f"{output_path.name}.part")
    partial.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(output_path)
    return report
