"""Tests for regime-conditioned strategy analysis."""

import csv

import pytest

from marketlab.regimes.analysis import maximum_episode_drawdown


def test_drawdown_does_not_stitch_disconnected_regime_episodes(tmp_path) -> None:
    results = tmp_path / "results.csv"
    with results.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "strategy", "daily_return"))
        writer.writeheader()
        writer.writerows(
            [
                {"date": "2024-01-01", "strategy": "test", "daily_return": 0.10},
                {"date": "2024-01-02", "strategy": "test", "daily_return": -0.20},
                {"date": "2024-01-03", "strategy": "test", "daily_return": -0.50},
                {"date": "2024-01-04", "strategy": "test", "daily_return": 0.10},
                {"date": "2024-01-05", "strategy": "test", "daily_return": -0.10},
            ]
        )
    regimes = {
        "2024-01-01": "bull",
        "2024-01-02": "bull",
        "2024-01-03": "bear",
        "2024-01-04": "bull",
        "2024-01-05": "bull",
    }

    result = maximum_episode_drawdown("test", "bull", results, regimes)

    assert result == pytest.approx(-0.20)
