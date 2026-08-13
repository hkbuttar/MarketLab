"""Alpha Vantage adapter for raw daily adjusted-price snapshots."""

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from marketlab.data.downloaders.base import SnapshotMetadata, save_snapshot, utc_now

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
DAILY_TIME_SERIES_KEY = "Time Series (Daily)"


class DownloaderConfigurationError(RuntimeError):
    """Raised when required provider configuration is absent."""


class InvalidProviderResponseError(ValueError):
    """Raised when a provider response cannot be persisted safely."""


class RawHttpResponse:
    """Minimal immutable HTTP response retained by provider adapters."""

    __slots__ = ("body", "status_code")

    def __init__(self, *, status_code: int, body: bytes) -> None:
        self.status_code = status_code
        self.body = body


HttpGet = Callable[[str, dict[str, str], float], RawHttpResponse]
Clock = Callable[[], datetime]


def _http_get(url: str, params: dict[str, str], timeout: float) -> RawHttpResponse:
    response = httpx.get(url, params=params, timeout=timeout)
    return RawHttpResponse(status_code=response.status_code, body=response.content)


class AlphaVantagePriceDownloader:
    """Download official daily adjusted-price API responses."""

    source = "alpha_vantage"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        raw_root: Path = Path("data/raw"),
        http_get: HttpGet = _http_get,
        clock: Clock = utc_now,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.raw_root = raw_root
        self._http_get = http_get
        self._clock = clock
        self.timeout = timeout

    def download(self, symbol: str) -> RawHttpResponse:
        """Fetch a full daily adjusted response without transforming its bytes."""

        if not self.api_key:
            raise DownloaderConfigurationError(
                "ALPHA_VANTAGE_API_KEY is required to download prices"
            )
        response = self._http_get(
            ALPHA_VANTAGE_URL,
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol.upper(),
                "outputsize": "full",
                "datatype": "json",
                "apikey": self.api_key,
            },
            self.timeout,
        )
        self.validate_response(response)
        return response

    def validate_response(self, response: RawHttpResponse) -> None:
        """Reject HTTP, API, and structurally unusable responses."""

        if response.status_code != httpx.codes.OK:
            raise InvalidProviderResponseError(
                f"Alpha Vantage returned HTTP {response.status_code}"
            )
        payload = _parse_json(response.body)
        for error_key in ("Error Message", "Information", "Note"):
            if error_key in payload:
                raise InvalidProviderResponseError(
                    f"Alpha Vantage rejected the request: {payload[error_key]}"
                )
        time_series = payload.get(DAILY_TIME_SERIES_KEY)
        if not isinstance(time_series, dict) or not time_series:
            raise InvalidProviderResponseError(
                "Alpha Vantage response has no daily time series"
            )

    def save_raw(self, response: RawHttpResponse, *, symbol: str) -> Path:
        """Save exact response bytes plus derived snapshot metadata."""

        self.validate_response(response)
        payload = _parse_json(response.body)
        time_series = payload[DAILY_TIME_SERIES_KEY]
        dates = sorted(time_series)
        downloaded_at = self._clock().astimezone(UTC).isoformat(timespec="seconds")
        return save_snapshot(
            content=response.body,
            metadata=SnapshotMetadata(
                source=self.source,
                downloaded_at=downloaded_at,
                rows=len(time_series),
                date_min=dates[0],
                date_max=dates[-1],
            ),
            raw_root=self.raw_root,
            category="prices",
            source=self.source,
            stem=symbol.upper(),
            suffix=".json",
        )

    def download_and_save(self, symbol: str) -> Path:
        """Download, validate the response envelope, and persist a snapshot."""

        return self.save_raw(self.download(symbol), symbol=symbol)


def _parse_json(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidProviderResponseError(
            "Alpha Vantage response is not valid JSON"
        ) from error
    if not isinstance(payload, dict):
        raise InvalidProviderResponseError(
            "Alpha Vantage response must be a JSON object"
        )
    return payload
