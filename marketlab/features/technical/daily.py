"""Streaming daily technical-feature generation."""

import csv
import gzip
import json
import math
from collections import deque
from pathlib import Path

from marketlab.data.schemas import PRICE_COLUMNS

TECHNICAL_COLUMNS = (
    "date",
    "symbol",
    "return_1d",
    "momentum_21",
    "momentum_63",
    "momentum_126",
    "momentum_252",
    "momentum_12_1",
    "trend_sma_50",
    "trend_sma_200",
    "trend_sma_50_200",
    "return_5d",
    "return_20d_zscore",
    "volatility_21",
    "volatility_63",
    "average_dollar_volume_21",
)


def build_daily_technical_features(source: Path, output: Path) -> dict[str, int]:
    """Stream adjusted-price features without crossing symbol boundaries."""

    if output.exists():
        raise FileExistsError(f"technical features already exist: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    rows = 0
    symbols = 0
    current_symbol = ""
    state = _RollingState()
    try:
        with (
            gzip.open(source, "rt", encoding="utf-8", newline="") as input_file,
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
        ):
            reader = csv.DictReader(input_file)
            if reader.fieldnames != list(PRICE_COLUMNS):
                raise ValueError("price columns do not match the canonical schema")
            writer = csv.DictWriter(output_file, fieldnames=TECHNICAL_COLUMNS)
            writer.writeheader()
            for row in reader:
                if row["symbol"] != current_symbol:
                    current_symbol = row["symbol"]
                    state = _RollingState()
                    symbols += 1
                writer.writerow(state.observe(row))
                rows += 1
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    result = {"rows": rows, "symbols": symbols}
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


class _RollingState:
    def __init__(self) -> None:
        self.prices: deque[float] = deque(maxlen=253)
        self.price_averages = {50: _RollingMoments(50), 200: _RollingMoments(200)}
        self.returns_21 = _RollingMoments(21)
        self.returns_63 = _RollingMoments(63)
        self.returns_20d = _RollingMoments(252)
        self.dollar_volume: deque[float] = deque(maxlen=21)
        self.dollar_volume_sum = 0.0

    def observe(self, row: dict[str, str]) -> dict[str, str]:
        adjusted = float(row["adjusted_close"])
        close = float(row["close"])
        volume = float(row["volume"])
        previous = self.prices[-1] if self.prices else None
        daily_return = adjusted / previous - 1 if previous else None
        self.prices.append(adjusted)
        for average in self.price_averages.values():
            average.append(adjusted)
        if daily_return is not None:
            self.returns_21.append(daily_return)
            self.returns_63.append(daily_return)
        dollar = close * volume
        if len(self.dollar_volume) == self.dollar_volume.maxlen:
            self.dollar_volume_sum -= self.dollar_volume[0]
        self.dollar_volume.append(dollar)
        self.dollar_volume_sum += dollar
        return_20d = self._momentum(20)
        if return_20d is not None:
            self.returns_20d.append(return_20d)
        return {
            "date": row["date"],
            "symbol": row["symbol"],
            "return_1d": _number(daily_return),
            "momentum_21": _number(self._momentum(21)),
            "momentum_63": _number(self._momentum(63)),
            "momentum_126": _number(self._momentum(126)),
            "momentum_252": _number(self._momentum(252)),
            "momentum_12_1": _number(self._momentum_12_1()),
            "trend_sma_50": _number(self._price_to_sma(50)),
            "trend_sma_200": _number(self._price_to_sma(200)),
            "trend_sma_50_200": _number(self._sma_spread()),
            "return_5d": _number(self._momentum(5)),
            "return_20d_zscore": _number(self._return_20d_zscore()),
            "volatility_21": _number(self.returns_21.volatility()),
            "volatility_63": _number(self.returns_63.volatility()),
            "average_dollar_volume_21": _number(
                self.dollar_volume_sum / 21 if len(self.dollar_volume) == 21 else None
            ),
        }

    def _momentum(self, sessions: int) -> float | None:
        if len(self.prices) <= sessions:
            return None
        return self.prices[-1] / self.prices[-sessions - 1] - 1

    def _momentum_12_1(self) -> float | None:
        if len(self.prices) < 253:
            return None
        return self.prices[-22] / self.prices[0] - 1

    def _price_to_sma(self, sessions: int) -> float | None:
        average = self.price_averages[sessions].mean(minimum=sessions)
        if average is None:
            return None
        return self.prices[-1] / average - 1

    def _sma_spread(self) -> float | None:
        short = self.price_averages[50].mean(minimum=50)
        long = self.price_averages[200].mean(minimum=200)
        if short is None or long is None:
            return None
        return short / long - 1

    def _return_20d_zscore(self) -> float | None:
        return self.returns_20d.zscore(minimum=20)


class _RollingMoments:
    def __init__(self, window: int) -> None:
        self.window = window
        self.values: deque[float] = deque(maxlen=window)
        self.total = 0.0
        self.total_squared = 0.0

    def append(self, value: float) -> None:
        if len(self.values) == self.window:
            removed = self.values[0]
            self.total -= removed
            self.total_squared -= removed * removed
        self.values.append(value)
        self.total += value
        self.total_squared += value * value

    def volatility(self) -> float | None:
        if len(self.values) != self.window:
            return None
        variance = (self.total_squared - self.total * self.total / self.window) / (
            self.window - 1
        )
        return math.sqrt(max(variance, 0) * 252)

    def mean(self, *, minimum: int = 1) -> float | None:
        """Return the rolling mean once the requested history is available."""

        return self.total / len(self.values) if len(self.values) >= minimum else None

    def zscore(self, *, minimum: int) -> float | None:
        """Standardize the latest observation against the backward-looking window."""

        count = len(self.values)
        if count < minimum:
            return None
        mean = self.total / count
        variance = (self.total_squared - self.total * self.total / count) / (count - 1)
        standard_deviation = math.sqrt(max(variance, 0.0))
        return (
            (self.values[-1] - mean) / standard_deviation if standard_deviation else 0.0
        )


def _number(value: float | None) -> str:
    return "" if value is None else format(value, ".15g")
