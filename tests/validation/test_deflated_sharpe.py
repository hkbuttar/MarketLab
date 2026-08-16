"""Tests for multiple-testing-adjusted Sharpe evidence."""

from marketlab.validation.deflated_sharpe import (
    deflated_sharpe_probability,
    expected_maximum_sharpe,
)


def test_expected_maximum_increases_with_search_dispersion() -> None:
    narrow = expected_maximum_sharpe([0.45, 0.50, 0.55, 0.60])
    wide = expected_maximum_sharpe([0.10, 0.30, 0.70, 0.90])

    assert wide > narrow > 0


def test_deflated_probability_rewards_more_observations_and_higher_sharpe() -> None:
    baseline = deflated_sharpe_probability(0.6, 0.5, 500, 0.0, 3.0)
    more_data = deflated_sharpe_probability(0.6, 0.5, 5_000, 0.0, 3.0)
    higher_sharpe = deflated_sharpe_probability(0.9, 0.5, 500, 0.0, 3.0)

    assert more_data > baseline
    assert higher_sharpe > baseline
