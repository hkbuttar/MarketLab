"""Tests for the point-in-time cross-sectional ML dataset."""

import csv
import io
from collections import defaultdict, deque

from marketlab.ml.dataset import (
    FEATURE_COLUMNS,
    ML_DATASET_COLUMNS,
    _process_date,
)


def _row(date: str, symbol: str, close: float, target: float) -> dict[str, str]:
    return {
        "date": date,
        "symbol": symbol,
        "close": str(close),
        "average_dollar_volume_21": "10000000",
        "forward_return_21": str(target),
        "momentum_12_1_rank": "0.7",
        "volatility_63_rank": "0.3",
        "book_to_market_rank": "0.6",
        "earnings_yield_rank": "0.8",
        "gross_profitability_rank": "0.9",
        "asset_growth_yoy_rank": "0.2",
    }


def test_dataset_uses_only_prior_closes_and_ranks_forward_target() -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=ML_DATASET_COLUMNS)
    writer.writeheader()
    histories = defaultdict(lambda: deque(maxlen=3))
    missing = {feature: 0 for feature in FEATURE_COLUMNS}
    for month in range(1, 5):
        _process_date(
            [
                _row(f"2024-{month:02d}-28", "AAA", 100 + month, -0.01),
                _row(f"2024-{month:02d}-28", "BBB", 200 + month, 0.02),
            ],
            histories,
            writer,
            missing,
        )
    rows = list(csv.DictReader(io.StringIO(buffer.getvalue())))

    assert rows[0]["trend_missing"] == "1"
    assert rows[0]["reversal_missing"] == "1"
    assert rows[-2]["trend_missing"] == "0"
    assert rows[-2]["reversal_missing"] == "0"
    assert float(rows[-2]["target_return_rank"]) == 0.5
    assert float(rows[-1]["target_return_rank"]) == 1.0
    assert "forward_return_21" not in FEATURE_COLUMNS
    assert "target_return_rank" not in FEATURE_COLUMNS
