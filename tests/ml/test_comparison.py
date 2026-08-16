from collections import defaultdict

import pytest

from marketlab.ml.comparison import _ml_month


def _rows(date: str, reverse: bool = False) -> list[dict[str, str]]:
    ranks = range(100) if not reverse else reversed(range(100))
    return [
        {
            "date": date,
            "model": "elastic_net",
            "symbol": f"S{symbol}",
            "predicted_rank": str(rank),
            "forward_return_21": str(symbol / 10_000.0),
        }
        for symbol, rank in enumerate(ranks)
    ]


def test_ml_month_applies_shared_selection_costs_and_turnover_limit() -> None:
    holdings: dict[str, dict[str, float]] = defaultdict(dict)
    benchmark = {"2020-01-31": 0.01, "2020-02-29": 0.02}
    risk_free = {"2020-01-31": 0.001, "2020-02-29": 0.001}

    first = _ml_month(
        ("elastic_net", "2020-01-31"),
        _rows("2020-01-31"),
        holdings,
        benchmark,
        risk_free,
        10.0,
    )
    second = _ml_month(
        ("elastic_net", "2020-02-29"),
        _rows("2020-02-29", reverse=True),
        holdings,
        benchmark,
        risk_free,
        10.0,
    )

    assert first["gross_return"] == pytest.approx(0.00895)
    assert first["turnover"] == pytest.approx(0.5)
    assert first["transaction_cost"] == pytest.approx(0.0005)
    assert first["net_return"] == pytest.approx(0.00845)
    assert second["turnover"] == pytest.approx(0.2)
