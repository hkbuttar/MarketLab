"""Tests for factor stability statistics."""

import pytest

from marketlab.factors.correlations import pearson_correlation
from marketlab.factors.tear_sheet import _series_summary


def test_pairwise_correlation_ignores_missing_values() -> None:
    result = pearson_correlation([1.0, None, 2.0, 3.0], [2.0, 99.0, 4.0, 6.0])

    assert result == pytest.approx(1.0)


def test_ic_summary_reports_consistency() -> None:
    result = _series_summary([0.1, 0.2, -0.1, 0.2])

    assert result["months"] == 4
    assert result["mean"] == pytest.approx(0.1)
    assert result["positive_rate"] == 0.75
