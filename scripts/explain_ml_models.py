"""Build walk-forward permutation, SHAP, and importance-stability reports."""

from pathlib import Path

from marketlab.ml.explainability import run_walk_forward_explainability


def main() -> int:
    report = run_walk_forward_explainability(
        Path("data/features/ml/cross_sectional_ranking.csv.gz"),
        Path("data/features/regimes/daily_regimes.csv"),
        Path("reports/ml/explainability"),
    )
    for model, features in report["models"].items():
        leaders = sorted(
            features.items(),
            key=lambda item: item[1]["mean_permutation_importance"],
            reverse=True,
        )[:3]
        print(model, ", ".join(name for name, _ in leaders))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
