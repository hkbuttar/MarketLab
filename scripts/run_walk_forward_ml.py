"""Run strict expanding-window training for the three ranking models."""

import argparse
from pathlib import Path

from marketlab.ml.models import MODEL_NAMES
from marketlab.ml.training import run_walk_forward_training


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=MODEL_NAMES)
    arguments = parser.parse_args()
    output = Path("data/features/ml/walk_forward_predictions.csv.gz")
    metadata = run_walk_forward_training(
        Path("data/features/ml/cross_sectional_ranking.csv.gz"),
        output,
        model_names=tuple(arguments.models),
    )
    print(f"Wrote {metadata['prediction_rows']:,} predictions to {output}")
    for fold in metadata["folds"]:
        print(
            fold["test_year"],
            f"train={fold['train_rows']:,}",
            f"test={fold['test_rows']:,}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
