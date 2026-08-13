"""Tests for Alpha Vantage listing, Treasury, and fundamental adapters."""

import json
from datetime import UTC, datetime
from pathlib import Path

from marketlab.data.downloaders import (
    AlphaVantageFundamentalDownloader,
    AlphaVantageListingDownloader,
    AlphaVantageTreasuryDownloader,
)
from marketlab.data.downloaders.alpha_vantage import RawHttpResponse


def fixed_clock() -> datetime:
    return datetime(2024, 2, 3, 12, 30, tzinfo=UTC)


def test_listing_downloader_preserves_csv(tmp_path: Path) -> None:
    body = (
        b"symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        b"AAPL,Apple Inc,NASDAQ,Stock,1980-12-12,null,Active\n"
    )
    response = RawHttpResponse(status_code=200, body=body)
    downloader = AlphaVantageListingDownloader(
        api_key="secret", raw_root=tmp_path, clock=fixed_clock
    )

    path = downloader.save_raw(response, state="active")

    assert path.read_bytes() == body
    assert "reference/alpha_vantage/listings_active" in str(path)


def test_treasury_downloader_records_observation_dates(tmp_path: Path) -> None:
    body = json.dumps(
        {
            "name": "3-Month Treasury Constant Maturity Rate",
            "data": [
                {"date": "2024-01-03", "value": "5.4"},
                {"date": "2024-01-02", "value": "5.4"},
            ],
        }
    ).encode()
    downloader = AlphaVantageTreasuryDownloader(
        api_key="secret", raw_root=tmp_path, clock=fixed_clock
    )

    path = downloader.save_raw(RawHttpResponse(status_code=200, body=body))
    metadata = json.loads(
        path.with_name("treasury_3month_daily.metadata.json").read_text()
    )

    assert metadata["rows"] == 2
    assert metadata["date_min"] == "2024-01-02"
    assert metadata["date_max"] == "2024-01-03"


def test_fundamental_downloader_preserves_reports(tmp_path: Path) -> None:
    body = json.dumps(
        {
            "symbol": "IBM",
            "annualReports": [{"fiscalDateEnding": "2023-12-31"}],
            "quarterlyReports": [{"fiscalDateEnding": "2024-03-31"}],
        }
    ).encode()
    downloader = AlphaVantageFundamentalDownloader(
        api_key="secret", raw_root=tmp_path, clock=fixed_clock
    )

    path = downloader.save_raw(
        RawHttpResponse(status_code=200, body=body),
        symbol="IBM",
        function="BALANCE_SHEET",
    )

    assert path.read_bytes() == body
    assert "IBM_balance_sheet" in str(path)
