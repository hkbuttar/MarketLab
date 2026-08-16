"""Strict expanding-window model training and prediction."""

import csv
import gzip
import json
from pathlib import Path

import numpy as np

from marketlab.ml.dataset import FEATURE_COLUMNS, ML_DATASET_COLUMNS
from marketlab.ml.models import MODEL_NAMES, create_ranking_model
from marketlab.validation.purging import load_benchmark_calendar, purged_train_indices

MODEL_FEATURE_COLUMNS = (
    *FEATURE_COLUMNS,
    *(f"{feature}_missing" for feature in FEATURE_COLUMNS),
)
PREDICTION_COLUMNS = (
    "date",
    "symbol",
    "model",
    "predicted_rank",
    "target_return_rank",
    "forward_return_21",
    "train_start",
    "train_end",
    "test_year",
)


def run_walk_forward_training(
    dataset_path: Path,
    output_path: Path,
    *,
    model_names: tuple[str, ...] = MODEL_NAMES,
    train_start_year: int = 2013,
    first_test_year: int = 2018,
    random_state: int = 1729,
    purge_calendar_path: Path | None = None,
    label_horizon_sessions: int = 21,
    embargo_sessions: int = 5,
) -> dict[str, object]:
    """Fit expanding yearly folds and atomically write out-of-sample predictions."""

    data = load_ml_dataset(dataset_path, minimum_year=train_start_year)
    folds = expanding_year_folds(
        data["dates"],
        train_start_year=train_start_year,
        first_test_year=first_test_year,
    )
    calendar = (
        load_benchmark_calendar(purge_calendar_path) if purge_calendar_path else None
    )
    if calendar:
        for fold in folds:
            original = fold["train_indices"]
            test_start = str(data["dates"][fold["test_indices"][0]])
            fold["train_indices"] = purged_train_indices(
                data["dates"],
                original,
                test_start,
                calendar,
                label_horizon_sessions=label_horizon_sessions,
                embargo_sessions=embargo_sessions,
            )
            fold["purged_rows"] = len(original) - len(fold["train_indices"])
    if not folds:
        raise ValueError("dataset contains no eligible walk-forward folds")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(f"{output_path.name}.part")
    fold_metadata: list[dict[str, object]] = []
    predictions_written = 0
    try:
        with gzip.open(partial, "wt", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=PREDICTION_COLUMNS)
            writer.writeheader()
            for fold in folds:
                train_indices = fold["train_indices"]
                test_indices = fold["test_indices"]
                for model_name in model_names:
                    model = create_ranking_model(model_name, random_state=random_state)
                    model.fit(
                        data["features"][train_indices], data["targets"][train_indices]
                    )
                    predictions = model.predict(data["features"][test_indices])
                    for index, prediction in zip(
                        test_indices, predictions, strict=True
                    ):
                        writer.writerow(
                            {
                                "date": data["dates"][index],
                                "symbol": data["symbols"][index],
                                "model": model_name,
                                "predicted_rank": prediction,
                                "target_return_rank": data["targets"][index],
                                "forward_return_21": data["forward_returns"][index],
                                "train_start": fold["train_start"],
                                "train_end": fold["train_end"],
                                "test_year": fold["test_year"],
                            }
                        )
                    predictions_written += len(test_indices)
                fold_metadata.append(
                    {
                        "test_year": fold["test_year"],
                        "train_start": fold["train_start"],
                        "train_end": fold["train_end"],
                        "train_rows": len(train_indices),
                        "test_rows": len(test_indices),
                        "purged_rows": fold.get("purged_rows", 0),
                    }
                )
        partial.replace(output_path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    metadata: dict[str, object] = {
        "method": (
            "purged expanding-window walk-forward"
            if calendar
            else "standard expanding-window walk-forward"
        ),
        "purged": bool(calendar),
        "label_horizon_sessions": label_horizon_sessions if calendar else 0,
        "embargo_sessions": embargo_sessions if calendar else 0,
        "models": list(model_names),
        "features": list(MODEL_FEATURE_COLUMNS),
        "target": "target_return_rank",
        "prediction_rows": predictions_written,
        "folds": fold_metadata,
    }
    metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
    metadata_partial = metadata_path.with_name(f"{metadata_path.name}.part")
    metadata_partial.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata_partial.replace(metadata_path)
    return metadata


def load_ml_dataset(path: Path, *, minimum_year: int) -> dict[str, np.ndarray]:
    """Load the compressed ranking dataset into compact typed arrays."""

    dates: list[str] = []
    symbols: list[str] = []
    features: list[list[float]] = []
    targets: list[float] = []
    forward_returns: list[float] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(ML_DATASET_COLUMNS):
            raise ValueError("ML dataset columns are not canonical")
        for row in reader:
            if int(row["date"][:4]) < minimum_year:
                continue
            dates.append(row["date"])
            symbols.append(row["symbol"])
            features.append(
                [
                    float(row[column]) if row[column] else np.nan
                    for column in MODEL_FEATURE_COLUMNS
                ]
            )
            targets.append(float(row["target_return_rank"]))
            forward_returns.append(float(row["forward_return_21"]))
    return {
        "dates": np.asarray(dates),
        "symbols": np.asarray(symbols),
        "features": np.asarray(features, dtype=np.float32),
        "targets": np.asarray(targets, dtype=np.float32),
        "forward_returns": np.asarray(forward_returns, dtype=np.float32),
    }


def expanding_year_folds(
    dates: np.ndarray,
    *,
    train_start_year: int,
    first_test_year: int,
) -> list[dict[str, object]]:
    """Return strict yearly train/test indices for an expanding window."""

    years = np.asarray([int(str(date)[:4]) for date in dates])
    maximum_year = int(years.max()) if len(years) else first_test_year - 1
    folds: list[dict[str, object]] = []
    for test_year in range(first_test_year, maximum_year + 1):
        train_indices = np.flatnonzero(
            (years >= train_start_year) & (years < test_year)
        )
        test_indices = np.flatnonzero(years == test_year)
        if not len(train_indices) or not len(test_indices):
            continue
        folds.append(
            {
                "test_year": test_year,
                "train_start": str(dates[train_indices[0]]),
                "train_end": str(dates[train_indices[-1]]),
                "train_indices": train_indices,
                "test_indices": test_indices,
            }
        )
    return folds
