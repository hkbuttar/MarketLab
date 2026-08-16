"""Tests for the transparent MarketLab robustness diagnostic."""

import pytest

from marketlab.validation.robustness_score import WEIGHTS, _scaled, _score_label


def test_component_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_scaled_component_is_bounded_and_score_labels_are_explicit() -> None:
    assert _scaled(-0.20, -0.10, 0.10) == 0.0
    assert _scaled(0.0, -0.10, 0.10) == pytest.approx(50.0)
    assert _scaled(0.20, -0.10, 0.10) == 100.0
    assert _score_label(75) == "strong"
    assert _score_label(60) == "moderate"
    assert _score_label(40) == "mixed"
    assert _score_label(39.9) == "weak"
