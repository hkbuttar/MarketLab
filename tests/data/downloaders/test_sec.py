"""Tests for SEC bulk archive acquisition."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from marketlab.data.downloaders import SecBulkDownloader, SecConfigurationError
from marketlab.data.downloaders.sec import SEC_ARCHIVES, RawSecResponse


def test_sec_downloader_sends_identifying_user_agent() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    def http_get(url: str, headers: dict[str, str], timeout: float) -> RawSecResponse:
        calls.append((url, headers, timeout))
        return RawSecResponse(status_code=200, body=b"PK zip")

    downloader = SecBulkDownloader(
        user_agent="MarketLab researcher@example.com", http_get=http_get
    )

    downloader.download("companyfacts")

    assert calls[0][0] == SEC_ARCHIVES["companyfacts"]
    assert calls[0][1]["User-Agent"] == "MarketLab researcher@example.com"


def test_sec_downloader_requires_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)

    with pytest.raises(SecConfigurationError, match="SEC_USER_AGENT"):
        SecBulkDownloader().download("companyfacts")


def test_sec_downloader_preserves_zip_bytes(tmp_path: Path) -> None:
    response = RawSecResponse(status_code=200, body=b"PK exact archive bytes")
    downloader = SecBulkDownloader(
        user_agent="MarketLab researcher@example.com",
        raw_root=tmp_path,
        clock=lambda: datetime(2024, 2, 3, 12, 30, tzinfo=UTC),
    )

    path = downloader.save_raw(response, archive="submissions")

    assert path.read_bytes() == response.body
    assert "fundamentals/sec_edgar/submissions" in str(path)
