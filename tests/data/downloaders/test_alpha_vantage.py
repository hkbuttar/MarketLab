"""Tests for raw Alpha Vantage price acquisition."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from marketlab.data.downloaders import (
    AlphaVantagePriceDownloader,
    DownloaderConfigurationError,
    InvalidProviderResponseError,
)
from marketlab.data.downloaders.alpha_vantage import (
    ALPHA_VANTAGE_URL,
    RawHttpResponse,
)


def response_body() -> bytes:
    return json.dumps(
        {
            "Meta Data": {"2. Symbol": "SPY"},
            "Time Series (Daily)": {
                "2024-01-03": {
                    "1. open": "100.0",
                    "2. high": "103.0",
                    "3. low": "99.0",
                    "4. close": "102.0",
                    "5. adjusted close": "101.5",
                    "6. volume": "1100000",
                },
                "2024-01-02": {
                    "1. open": "99.0",
                    "2. high": "102.0",
                    "3. low": "98.0",
                    "4. close": "101.0",
                    "5. adjusted close": "100.5",
                    "6. volume": "1000000",
                },
            },
        },
        separators=(",", ":"),
    ).encode()


def test_download_calls_official_adjusted_daily_endpoint() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []
    expected = RawHttpResponse(status_code=200, body=response_body())

    def http_get(url: str, params: dict[str, str], timeout: float) -> RawHttpResponse:
        calls.append((url, params, timeout))
        return expected

    downloader = AlphaVantagePriceDownloader(api_key="secret", http_get=http_get)

    assert downloader.download("spy") is expected
    assert calls == [
        (
            ALPHA_VANTAGE_URL,
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": "SPY",
                "outputsize": "full",
                "datatype": "json",
                "apikey": "secret",
            },
            30.0,
        )
    ]


def test_download_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    with pytest.raises(DownloaderConfigurationError, match="API_KEY"):
        AlphaVantagePriceDownloader().download("SPY")


def test_save_raw_preserves_response_bytes_and_writes_metadata(
    tmp_path: Path,
) -> None:
    downloaded_at = datetime(2024, 2, 3, 12, 30, tzinfo=UTC)
    downloader = AlphaVantagePriceDownloader(
        api_key="secret", raw_root=tmp_path, clock=lambda: downloaded_at
    )
    response = RawHttpResponse(status_code=200, body=response_body())

    data_path = downloader.save_raw(response, symbol="spy")

    assert data_path == (
        tmp_path / "prices/alpha_vantage/SPY/2024-02-03T123000Z/SPY.json"
    )
    assert data_path.read_bytes() == response.body
    metadata = json.loads(
        data_path.with_name("SPY.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata == {
        "source": "alpha_vantage",
        "downloaded_at": "2024-02-03T12:30:00+00:00",
        "rows": 2,
        "date_min": "2024-01-02",
        "date_max": "2024-01-03",
    }


@pytest.mark.parametrize(
    "response",
    [
        RawHttpResponse(status_code=503, body=b"unavailable"),
        RawHttpResponse(status_code=200, body=b"not-json"),
        RawHttpResponse(status_code=200, body=b'{"Note":"rate limited"}'),
        RawHttpResponse(status_code=200, body=b'{"Meta Data":{}}'),
    ],
)
def test_validate_response_rejects_provider_errors(
    response: RawHttpResponse,
) -> None:
    with pytest.raises(InvalidProviderResponseError):
        AlphaVantagePriceDownloader(api_key="secret").validate_response(response)
