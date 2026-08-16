"""Load immutable Alpha Vantage snapshots into canonical records."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from marketlab.data.schemas import PriceRecord

DAILY_TIME_SERIES_KEY = "Time Series (Daily)"
PRICE_FIELDS = {
    "open": "1. open",
    "high": "2. high",
    "low": "3. low",
    "close": "4. close",
    "adjusted_close": "5. adjusted close",
    "volume": "6. volume",
}


class InvalidSnapshotError(ValueError):
    """Raised when a raw snapshot cannot produce canonical records."""


def load_alpha_vantage_prices(path: Path) -> list[PriceRecord]:
    """Parse one raw daily-adjusted snapshot in ascending date order."""

    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        message = f"cannot read Alpha Vantage snapshot: {path}"
        raise InvalidSnapshotError(message) from error

    if not isinstance(payload, dict):
        raise InvalidSnapshotError("Alpha Vantage snapshot must be a JSON object")

    metadata = payload.get("Meta Data")
    time_series = payload.get(DAILY_TIME_SERIES_KEY)
    if not isinstance(metadata, dict) or not isinstance(time_series, dict):
        raise InvalidSnapshotError("Alpha Vantage snapshot is missing price data")

    symbol = metadata.get("2. Symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidSnapshotError("Alpha Vantage snapshot is missing its symbol")

    records = [
        _price_record(symbol.strip().upper(), date_text, observation)
        for date_text, observation in time_series.items()
    ]
    records.sort(key=lambda record: record.date)
    return records


def _price_record(symbol: str, date_text: str, observation: object) -> PriceRecord:
    if not isinstance(observation, dict):
        message = f"price observation for {date_text} is not an object"
        raise InvalidSnapshotError(message)
    try:
        return PriceRecord(
            date=datetime.strptime(date_text, "%Y-%m-%d"),
            symbol=symbol,
            open=float(observation[PRICE_FIELDS["open"]]),
            high=float(observation[PRICE_FIELDS["high"]]),
            low=float(observation[PRICE_FIELDS["low"]]),
            close=float(observation[PRICE_FIELDS["close"]]),
            adjusted_close=float(observation[PRICE_FIELDS["adjusted_close"]]),
            volume=int(observation[PRICE_FIELDS["volume"]]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidSnapshotError(
            f"invalid Alpha Vantage price observation for {date_text}"
        ) from error
