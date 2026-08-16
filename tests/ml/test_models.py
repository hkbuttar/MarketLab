"""Tests for the constrained ranking-model registry."""

import numpy as np
import pytest

from marketlab.ml.models import MODEL_NAMES, create_ranking_model


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_supported_models_fit_missing_features_and_predict_deterministically(
    name,
) -> None:
    features = np.array(
        [
            [index / 40, np.nan if index % 7 == 0 else (index % 5) / 5]
            for index in range(40)
        ]
    )
    target = np.array([index / 40 for index in range(40)])
    first = create_ranking_model(name, random_state=7).fit(features, target)
    second = create_ranking_model(name, random_state=7).fit(features, target)

    first_predictions = first.predict(features)
    second_predictions = second.predict(features)

    assert first_predictions.shape == (40,)
    assert np.all(np.isfinite(first_predictions))
    assert np.allclose(first_predictions, second_predictions)


def test_model_registry_rejects_unbounded_model_expansion() -> None:
    with pytest.raises(ValueError, match="unsupported ranking model"):
        create_ranking_model("neural_network")
