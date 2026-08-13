"""Tests for streaming SEC bulk archive acquisition."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest

from marketlab.data.downloaders import SecBulkDownloader, SecConfigurationError
from marketlab.data.downloaders.sec import (
    SEC_ARCHIVES,
    InvalidSecResponseError,
    RawSecStream,
)


def test_sec_downloader_sends_identifying_user_agent() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    @contextmanager
    def http_stream(
        url: str, headers: dict[str, str], timeout: float
    ) -> Iterator[RawSecStream]:
        calls.append((url, headers, timeout))
        yield RawSecStream(status_code=200, headers={}, chunks=[b"PK zip"])

    downloader = SecBulkDownloader(
        user_agent="MarketLab researcher@example.com", http_stream=http_stream
    )

    with downloader.download("companyfacts"):
        pass

    assert calls[0][0] == SEC_ARCHIVES["companyfacts"]
    assert calls[0][1]["User-Agent"] == "MarketLab researcher@example.com"


def test_sec_downloader_requires_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)

    with pytest.raises(SecConfigurationError, match="SEC_USER_AGENT"):
        SecBulkDownloader().download("companyfacts")


def test_sec_downloader_streams_chunks_and_finalizes_atomically(
    tmp_path: Path,
) -> None:
    response = RawSecStream(
        status_code=200,
        headers={"content-length": "22"},
        chunks=[b"P", b"K exact ", b"archive bytes"],
    )
    downloader = SecBulkDownloader(
        user_agent="MarketLab researcher@example.com",
        raw_root=tmp_path,
        clock=lambda: datetime(2024, 2, 3, 12, 30, tzinfo=UTC),
        disk_reserve_bytes=0,
    )

    path = downloader.save_raw(response, archive="submissions")

    assert path.read_bytes() == b"PK exact archive bytes"
    assert "fundamentals/sec_edgar/submissions" in str(path)
    assert not path.with_suffix(".zip.part").exists()
    assert path.with_name("submissions.metadata.json").exists()


def test_sec_downloader_removes_partial_non_zip(tmp_path: Path) -> None:
    response = RawSecStream(status_code=200, headers={}, chunks=[b"not a zip"])
    downloader = SecBulkDownloader(
        user_agent="MarketLab researcher@example.com",
        raw_root=tmp_path,
        disk_reserve_bytes=0,
    )

    with pytest.raises(InvalidSecResponseError, match="ZIP"):
        downloader.save_raw(response, archive="companyfacts")

    assert not list(tmp_path.rglob("*.part"))
    assert not list(tmp_path.rglob("*.zip"))
