"""Tests for walk-forward feature-importance stability."""

import numpy as np

from marketlab.ml.explainability import _sample_indices, summarize_importance_stability


def test_deterministic_sample_spans_complete_index_range() -> None:
    result = _sample_indices(np.arange(100), 5)

    assert list(result) == [0, 24, 49, 74, 99]


def test_importance_summary_tracks_top_feature_frequency() -> None:
    rows = []
    for year, first, second in ((2020, 0.3, 0.1), (2021, 0.2, 0.4)):
        rows.extend(
            [
                {
                    "test_year": year,
                    "model": "linear",
                    "feature": "momentum",
                    "permutation_importance_mean": first,
                    "mean_absolute_shap": abs(first),
                },
                {
                    "test_year": year,
                    "model": "linear",
                    "feature": "value",
                    "permutation_importance_mean": second,
                    "mean_absolute_shap": abs(second),
                },
            ]
        )

    summary = summarize_importance_stability(rows)

    assert summary["linear"]["momentum"]["top_three_year_fraction"] == 1.0
    assert summary["linear"]["value"]["top_three_year_fraction"] == 1.0
    assert summary["linear"]["momentum"]["mean_permutation_importance"] == 0.25
