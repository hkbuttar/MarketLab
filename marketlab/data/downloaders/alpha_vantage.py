"""Alpha Vantage adapter for raw daily adjusted-price snapshots."""

import json
import os
from collections.abc import Callable
from csv import DictReader
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import httpx

from marketlab.data.downloaders.base import SnapshotMetadata, save_snapshot, utc_now

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
DAILY_TIME_SERIES_KEY = "Time Series (Daily)"
FUNDAMENTAL_FUNCTIONS = (
    "OVERVIEW",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW",
    "SHARES_OUTSTANDING",
)


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


class AlphaVantageListingDownloader:
    """Download active or delisted U.S. security listings as raw CSV."""

    source = "alpha_vantage"
    required_columns = {
        "symbol",
        "name",
        "exchange",
        "assetType",
        "ipoDate",
        "delistingDate",
        "status",
    }

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

    def download(self, *, state: str) -> RawHttpResponse:
        """Fetch the latest active list or complete delisted list."""

        if state not in {"active", "delisted"}:
            raise ValueError("state must be 'active' or 'delisted'")
        _require_api_key(self.api_key)
        response = self._http_get(
            ALPHA_VANTAGE_URL,
            {"function": "LISTING_STATUS", "state": state, "apikey": self.api_key},
            self.timeout,
        )
        self.validate_response(response)
        return response

    def validate_response(self, response: RawHttpResponse) -> None:
        """Reject HTTP, API, and malformed listing responses."""

        _require_ok(response)
        _reject_json_error(response.body)
        rows = _csv_rows(response.body)
        if not rows:
            raise InvalidProviderResponseError("Alpha Vantage returned no listings")
        missing = self.required_columns.difference(rows[0])
        if missing:
            missing_names = ", ".join(sorted(missing))
            raise InvalidProviderResponseError(
                f"Alpha Vantage listing is missing columns: {missing_names}"
            )

    def save_raw(self, response: RawHttpResponse, *, state: str) -> Path:
        """Save exact listing CSV bytes plus snapshot metadata."""

        self.validate_response(response)
        rows = _csv_rows(response.body)
        dates = sorted(
            row["ipoDate"]
            for row in rows
            if row.get("ipoDate") and row["ipoDate"] != "null"
        )
        return save_snapshot(
            content=response.body,
            metadata=_metadata(
                self.source,
                self._clock,
                len(rows),
                dates[0] if dates else None,
                dates[-1] if dates else None,
            ),
            raw_root=self.raw_root,
            category="reference",
            source=self.source,
            stem=f"listings_{state}",
            suffix=".csv",
        )

    def download_and_save(self, *, state: str) -> Path:
        return self.save_raw(self.download(state=state), state=state)


class AlphaVantageTreasuryDownloader:
    """Download the daily three-month Treasury yield series."""

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

    def download(self) -> RawHttpResponse:
        _require_api_key(self.api_key)
        response = self._http_get(
            ALPHA_VANTAGE_URL,
            {
                "function": "TREASURY_YIELD",
                "interval": "daily",
                "maturity": "3month",
                "apikey": self.api_key,
            },
            self.timeout,
        )
        self.validate_response(response)
        return response

    def validate_response(self, response: RawHttpResponse) -> None:
        _require_ok(response)
        payload = _parse_json(response.body)
        _reject_payload_error(payload)
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            raise InvalidProviderResponseError(
                "Alpha Vantage response has no Treasury observations"
            )

    def save_raw(self, response: RawHttpResponse) -> Path:
        self.validate_response(response)
        payload = _parse_json(response.body)
        data = payload["data"]
        dates = sorted(item["date"] for item in data)
        return save_snapshot(
            content=response.body,
            metadata=_metadata(
                self.source, self._clock, len(data), dates[0], dates[-1]
            ),
            raw_root=self.raw_root,
            category="reference",
            source=self.source,
            stem="treasury_3month_daily",
            suffix=".json",
        )

    def download_and_save(self) -> Path:
        return self.save_raw(self.download())


class AlphaVantageFundamentalDownloader:
    """Download provider-shaped company metadata and financial statements."""

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

    def download(self, symbol: str, *, function: str) -> RawHttpResponse:
        if function not in FUNDAMENTAL_FUNCTIONS:
            raise ValueError(f"unsupported fundamental function: {function}")
        _require_api_key(self.api_key)
        response = self._http_get(
            ALPHA_VANTAGE_URL,
            {"function": function, "symbol": symbol.upper(), "apikey": self.api_key},
            self.timeout,
        )
        self.validate_response(response)
        return response

    def validate_response(self, response: RawHttpResponse) -> None:
        _require_ok(response)
        payload = _parse_json(response.body)
        _reject_payload_error(payload)
        if not payload:
            raise InvalidProviderResponseError(
                "Alpha Vantage returned an empty fundamental response"
            )

    def save_raw(
        self, response: RawHttpResponse, *, symbol: str, function: str
    ) -> Path:
        self.validate_response(response)
        payload = _parse_json(response.body)
        reports = [
            report
            for key in ("annualReports", "quarterlyReports")
            if isinstance(payload.get(key), list)
            for report in payload[key]
        ]
        dates = sorted(
            report["fiscalDateEnding"]
            for report in reports
            if report.get("fiscalDateEnding")
        )
        return save_snapshot(
            content=response.body,
            metadata=_metadata(
                self.source,
                self._clock,
                len(reports) if reports else 1,
                dates[0] if dates else None,
                dates[-1] if dates else None,
            ),
            raw_root=self.raw_root,
            category="fundamentals",
            source=self.source,
            stem=f"{symbol.upper()}_{function.lower()}",
            suffix=".json",
        )

    def download_and_save(self, symbol: str, *, function: str) -> Path:
        return self.save_raw(
            self.download(symbol, function=function),
            symbol=symbol,
            function=function,
        )


def _require_api_key(api_key: str) -> None:
    if not api_key:
        raise DownloaderConfigurationError(
            "ALPHA_VANTAGE_API_KEY is required to download data"
        )


def _require_ok(response: RawHttpResponse) -> None:
    if response.status_code != httpx.codes.OK:
        raise InvalidProviderResponseError(
            f"Alpha Vantage returned HTTP {response.status_code}"
        )


def _reject_payload_error(payload: dict[str, Any]) -> None:
    for error_key in ("Error Message", "Information", "Note"):
        if error_key in payload:
            raise InvalidProviderResponseError(
                f"Alpha Vantage rejected the request: {payload[error_key]}"
            )


def _reject_json_error(body: bytes) -> None:
    if body.lstrip().startswith(b"{"):
        _reject_payload_error(_parse_json(body))


def _csv_rows(body: bytes) -> list[dict[str, str]]:
    try:
        return list(DictReader(StringIO(body.decode("utf-8-sig"))))
    except UnicodeDecodeError as error:
        raise InvalidProviderResponseError(
            "Alpha Vantage listing is not valid UTF-8"
        ) from error


def _metadata(
    source: str,
    clock: Clock,
    rows: int,
    date_min: str | None,
    date_max: str | None,
) -> SnapshotMetadata:
    return SnapshotMetadata(
        source=source,
        downloaded_at=clock().astimezone(UTC).isoformat(timespec="seconds"),
        rows=rows,
        date_min=date_min,
        date_max=date_max,
    )


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
