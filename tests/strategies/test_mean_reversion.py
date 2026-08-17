import pytest

from marketlab.strategies import MEAN_REVERSION, STRATEGIES
from marketlab.strategies.base import composite_score


def test_mean_reversion_prefers_recent_losers() -> None:
    loser = composite_score({"return_20d_zscore_rank": "0.1"}, MEAN_REVERSION)
    winner = composite_score({"return_20d_zscore_rank": "0.9"}, MEAN_REVERSION)

    assert loser == pytest.approx(0.9)
    assert winner == pytest.approx(0.1)
    assert loser > winner


def test_mean_reversion_records_high_turnover_weekly_design() -> None:
    assert STRATEGIES["mean_reversion"] is MEAN_REVERSION
    assert MEAN_REVERSION.rebalance_frequency == "weekly"
    assert MEAN_REVERSION.maximum_turnover == pytest.approx(0.5)
    assert MEAN_REVERSION.signal_delay_sessions == 1
