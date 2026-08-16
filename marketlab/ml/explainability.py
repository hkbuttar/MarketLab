"""Walk-forward permutation, SHAP, and feature-stability analysis."""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.inspection import permutation_importance

from marketlab.factors.information_coefficient import spearman_ic
from marketlab.ml.models import MODEL_NAMES, create_ranking_model
from marketlab.ml.training import (
    MODEL_FEATURE_COLUMNS,
    expanding_year_folds,
    load_ml_dataset,
)
from marketlab.validation.purging import load_benchmark_calendar, purged_train_indices

IMPORTANCE_COLUMNS = (
    "test_year",
    "model",
    "feature",
    "permutation_importance_mean",
    "permutation_importance_std",
    "mean_absolute_shap",
    "train_rows",
    "test_rows",
)


def run_walk_forward_explainability(
    dataset_path: Path,
    calendar_path: Path,
    output_directory: Path,
    *,
    train_start_year: int = 2013,
    first_test_year: int = 2018,
    permutation_sample_size: int = 1_000,
    shap_sample_size: int = 100,
    permutation_repeats: int = 2,
    random_state: int = 1729,
) -> dict[str, object]:
    """Refit purged folds and calculate OOS feature importance by year."""

    data = load_ml_dataset(dataset_path, minimum_year=train_start_year)
    folds = expanding_year_folds(
        data["dates"],
        train_start_year=train_start_year,
        first_test_year=first_test_year,
    )
    calendar = load_benchmark_calendar(calendar_path)
    rows: list[dict[str, object]] = []
    for fold in folds:
        candidates = fold["train_indices"]
        test_indices = fold["test_indices"]
        test_start = str(data["dates"][test_indices[0]])
        train_indices = purged_train_indices(
            data["dates"],
            candidates,
            test_start,
            calendar,
            label_horizon_sessions=21,
            embargo_sessions=5,
        )
        permutation_indices = _sample_indices(test_indices, permutation_sample_size)
        shap_indices = _sample_indices(test_indices, shap_sample_size)
        for model_name in MODEL_NAMES:
            model = create_ranking_model(model_name, random_state=random_state)
            model.fit(data["features"][train_indices], data["targets"][train_indices])
            permutation = permutation_importance(
                model,
                data["features"][permutation_indices],
                data["targets"][permutation_indices],
                scoring=_rank_ic_scorer,
                n_repeats=permutation_repeats,
                random_state=random_state,
                n_jobs=1,
            )
            shap_values = _mean_absolute_shap(
                model_name,
                model,
                data["features"][train_indices],
                data["features"][shap_indices],
            )
            for index, feature in enumerate(MODEL_FEATURE_COLUMNS):
                rows.append(
                    {
                        "test_year": fold["test_year"],
                        "model": model_name,
                        "feature": feature,
                        "permutation_importance_mean": permutation.importances_mean[
                            index
                        ],
                        "permutation_importance_std": permutation.importances_std[
                            index
                        ],
                        "mean_absolute_shap": shap_values[index],
                        "train_rows": len(train_indices),
                        "test_rows": len(test_indices),
                    }
                )
    summary: dict[str, object] = {
        "method": "purged walk-forward OOS permutation importance and SHAP",
        "permutation_sample_size": permutation_sample_size,
        "shap_sample_size": shap_sample_size,
        "permutation_repeats": permutation_repeats,
        "models": summarize_importance_stability(rows),
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_csv(output_directory / "feature_importance_by_year.csv", rows)
    _write_json(output_directory / "feature_importance_stability.json", summary)
    return summary


def _rank_ic_scorer(estimator, features: np.ndarray, target: np.ndarray) -> float:
    predictions = estimator.predict(features)
    return spearman_ic(list(predictions), list(target)) or 0.0


def _mean_absolute_shap(
    model_name: str,
    pipeline,
    train_features: np.ndarray,
    test_features: np.ndarray,
) -> np.ndarray:
    import shap

    transformed_test = pipeline[:-1].transform(test_features)
    estimator = pipeline.named_steps["regressor"]
    if model_name == "elastic_net":
        background_indices = _sample_indices(
            np.arange(len(train_features)), min(100, len(train_features))
        )
        background = pipeline[:-1].transform(train_features[background_indices])
        explainer = shap.LinearExplainer(estimator, background)
    else:
        explainer = shap.TreeExplainer(estimator)
    values = explainer.shap_values(transformed_test)
    return np.mean(np.abs(np.asarray(values)), axis=0)


def summarize_importance_stability(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    values: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    by_period: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        values[(str(row["model"]), str(row["feature"]))].append(row)
        by_period[(str(row["model"]), int(row["test_year"]))].append(row)
    top_features = {
        key: {
            str(item["feature"])
            for item in sorted(
                period_rows,
                key=lambda item: float(item["permutation_importance_mean"]),
                reverse=True,
            )[:3]
        }
        for key, period_rows in by_period.items()
    }
    result: dict[str, dict[str, object]] = defaultdict(dict)
    for (model, feature), feature_rows in sorted(values.items()):
        permutation = [
            float(row["permutation_importance_mean"]) for row in feature_rows
        ]
        shap_values = [float(row["mean_absolute_shap"]) for row in feature_rows]
        years = [int(row["test_year"]) for row in feature_rows]
        result[model][feature] = {
            "mean_permutation_importance": statistics.mean(permutation),
            "permutation_stability": 1.0 / (1.0 + statistics.pstdev(permutation)),
            "mean_absolute_shap": statistics.mean(shap_values),
            "shap_stability": 1.0 / (1.0 + statistics.pstdev(shap_values)),
            "top_three_year_fraction": sum(
                feature in top_features[(model, year)] for year in years
            )
            / len(years),
        }
    return dict(result)


def _sample_indices(indices: np.ndarray, maximum: int) -> np.ndarray:
    if len(indices) <= maximum:
        return indices
    positions = np.linspace(0, len(indices) - 1, maximum, dtype=int)
    return indices[positions]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=IMPORTANCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
