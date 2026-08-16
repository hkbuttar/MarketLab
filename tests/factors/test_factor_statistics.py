"""Tests for factor ranking and diagnostics."""

import pytest

from marketlab.factors.information_coefficient import spearman_ic
from marketlab.factors.quantiles import quantile_mean_returns
from marketlab.factors.ranking import percentile_ranks, quantile


def test_average_tie_ranks_and_quantiles() -> None:
    ranks = percentile_ranks([10.0, 20.0, 20.0, None, 40.0])

    assert ranks == [0.25, 0.625, 0.625, None, 1.0]
    assert [quantile(rank) for rank in ranks] == [2, 4, 4, None, 5]


def test_spearman_ic_and_quantile_returns() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    forward = [0.01, 0.02, 0.03, 0.04]

    assert spearman_ic(values, forward) == pytest.approx(1.0)
    assert quantile_mean_returns([1, 1, 5, 5], forward) == {
        1: pytest.approx(0.015),
        5: pytest.approx(0.035),
    }
