"""Tests for transparent point-in-time regime classification."""

import math

from marketlab.regimes.classifier import _label, classify_regimes


def test_regime_labels_cover_four_transparent_states() -> None:
    assert _label(101, 100, 0.1, 0.2)[2] == "bull_low_vol"
    assert _label(101, 100, 0.3, 0.2)[2] == "bull_high_vol"
    assert _label(99, 100, 0.1, 0.2)[2] == "bear_low_vol"
    assert _label(99, 100, 0.3, 0.2)[2] == "bear_high_vol"


def test_future_prices_do_not_change_existing_regimes() -> None:
    prices = [
        (f"session-{index:04d}", 100.0 + index * 0.03 + math.sin(index / 7.0))
        for index in range(520)
    ]

    original = classify_regimes(prices)
    extended = classify_regimes([*prices, ("future", 1_000.0)])

    assert original
    assert extended[: len(original)] == original
    assert original[0]["date"] == "session-0451"
