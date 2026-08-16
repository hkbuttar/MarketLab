"""Purging and embargo controls plus prediction comparisons."""

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from marketlab.factors.information_coefficient import spearman_ic


def purged_train_indices(
    dates: np.ndarray,
    candidate_indices: np.ndarray,
    test_start: str,
    calendar: list[str],
    *,
    label_horizon_sessions: int = 21,
    embargo_sessions: int = 5,
) -> np.ndarray:
    """Remove rows whose label horizon or embargo reaches the test interval."""

    positions = {date: index for index, date in enumerate(calendar)}
    if test_start not in positions:
        raise ValueError(f"test start is absent from benchmark calendar: {test_start}")
    boundary = calendar[max(0, positions[test_start] - embargo_sessions)]
    kept: list[int] = []
    for index in candidate_indices:
        date = str(dates[index])
        position = positions.get(date)
        if position is None:
            continue
        label_end = calendar[min(position + label_horizon_sessions, len(calendar) - 1)]
        if label_end < boundary:
            kept.append(int(index))
    return np.asarray(kept, dtype=int)


def load_benchmark_calendar(path: Path) -> list[str]:
    """Load the ordered daily regime/benchmark calendar."""

    with path.open(encoding="utf-8", newline="") as file:
        return [row["date"] for row in csv.DictReader(file)]


def compare_walk_forward_predictions(
    standard_path: Path, purged_path: Path, output_path: Path
) -> dict[str, object]:
    """Compare mean monthly rank IC and top-quintile realized return."""

    standard = _prediction_metrics(standard_path)
    purged = _prediction_metrics(purged_path)
    models = sorted(set(standard) | set(purged))
    comparison = {
        model: {
            "standard": standard[model],
            "purged": purged[model],
            "delta_mean_monthly_ic": (
                purged[model]["mean_monthly_ic"] - standard[model]["mean_monthly_ic"]
            ),
            "delta_top_quintile_return": (
                purged[model]["mean_top_quintile_return"]
                - standard[model]["mean_top_quintile_return"]
            ),
        }
        for model in models
    }
    report: dict[str, object] = {
        "method": (
            "standard versus 21-session-purged, 5-session-embargoed walk-forward"
        ),
        "models": comparison,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(f"{output_path.name}.part")
    partial.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(output_path)
    return report


def _prediction_metrics(path: Path) -> dict[str, dict[str, float | int]]:
    values: dict[tuple[str, str], list[tuple[float, float, float]]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            values[(row["model"], row["date"])].append(
                (
                    float(row["predicted_rank"]),
                    float(row["target_return_rank"]),
                    float(row["forward_return_21"]),
                )
            )
    ics: dict[str, list[float]] = defaultdict(list)
    top_returns: dict[str, list[float]] = defaultdict(list)
    for (model, _), rows in values.items():
        predictions = [row[0] for row in rows]
        targets = [row[1] for row in rows]
        ic = spearman_ic(predictions, targets)
        if ic is not None:
            ics[model].append(ic)
        count = max(1, int(len(rows) * 0.20))
        selected = sorted(rows, key=lambda row: row[0], reverse=True)[:count]
        top_returns[model].append(sum(row[2] for row in selected) / len(selected))
    return {
        model: {
            "months": len(model_ics),
            "mean_monthly_ic": sum(model_ics) / len(model_ics),
            "mean_top_quintile_return": sum(top_returns[model])
            / len(top_returns[model]),
        }
        for model, model_ics in ics.items()
    }
