"""Tests for robust factor preprocessing."""

from marketlab.features.preprocessing import winsorize


def test_winsorizes_cross_section_and_preserves_missing_values() -> None:
    values = [None, *[float(value) for value in range(100)], 10_000.0]

    result = winsorize(values)

    assert result[0] is None
    assert result[-1] < 10_000
    assert result[1] > 0
