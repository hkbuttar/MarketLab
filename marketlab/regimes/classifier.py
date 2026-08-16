"""Transparent, point-in-time market-regime classification."""

import csv
import gzip
import json
import math
import statistics
from collections import deque
from pathlib import Path

REGIME_COLUMNS = (
    "date",
    "benchmark_adjusted_close",
    "trend_sma_200",
    "realized_volatility_21",
    "volatility_threshold_252",
    "trend_state",
    "volatility_state",
    "regime",
)


def build_regime_dataset(prices_path: Path, output_path: Path) -> dict[str, object]:
    """Extract SPY prices, classify regimes, and atomically save observations."""

    prices: list[tuple[str, float]] = []
    with gzip.open(prices_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["symbol"] == "SPY":
                prices.append((row["date"], float(row["adjusted_close"])))
    rows = classify_regimes(prices)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(f"{output_path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REGIME_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(output_path)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["regime"]] = counts.get(row["regime"], 0) + 1
    metadata: dict[str, object] = {
        "benchmark": "SPY",
        "trend_window": 200,
        "volatility_window": 21,
        "volatility_threshold_window": 252,
        "threshold_lag_sessions": 1,
        "observations": len(rows),
        "regime_counts": counts,
    }
    output_path.with_suffix(output_path.suffix + ".metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def classify_regimes(prices: list[tuple[str, float]]) -> list[dict[str, object]]:
    """Classify each eligible day without using future observations."""

    closes: deque[float] = deque(maxlen=200)
    returns: deque[float] = deque(maxlen=21)
    volatility_history: deque[float] = deque(maxlen=252)
    previous: float | None = None
    result: list[dict[str, object]] = []
    for date, close in prices:
        daily_return = close / previous - 1.0 if previous else None
        previous = close
        closes.append(close)
        if daily_return is not None:
            returns.append(daily_return)
        if len(closes) < 200 or len(returns) < 21:
            continue
        trend = sum(closes) / len(closes)
        volatility = _sample_std(list(returns)) * math.sqrt(252.0)
        if len(volatility_history) < 252:
            volatility_history.append(volatility)
            continue
        threshold = statistics.median(volatility_history)
        trend_state, volatility_state, regime = _label(
            close, trend, volatility, threshold
        )
        result.append(
            {
                "date": date,
                "benchmark_adjusted_close": close,
                "trend_sma_200": trend,
                "realized_volatility_21": volatility,
                "volatility_threshold_252": threshold,
                "trend_state": trend_state,
                "volatility_state": volatility_state,
                "regime": regime,
            }
        )
        volatility_history.append(volatility)
    return result


def _label(
    close: float, trend: float, volatility: float, threshold: float
) -> tuple[str, str, str]:
    trend_state = "bull" if close >= trend else "bear"
    volatility_state = "high_vol" if volatility > threshold else "low_vol"
    return trend_state, volatility_state, f"{trend_state}_{volatility_state}"


def _sample_std(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
