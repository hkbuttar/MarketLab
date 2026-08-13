"""SEC EDGAR bulk archive downloader for filing-aware fundamentals."""

import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx

from marketlab.data.downloaders.base import SnapshotMetadata, save_snapshot, utc_now

SEC_ARCHIVES = {
    "companyfacts": "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip",
    "submissions": "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
}


class SecConfigurationError(RuntimeError):
    """Raised when the SEC-required identifying user agent is absent."""


class InvalidSecResponseError(ValueError):
    """Raised when an SEC bulk response is unusable."""


class RawSecResponse:
    """Minimal SEC response retained for exact-byte persistence."""

    __slots__ = ("body", "status_code")

    def __init__(self, *, status_code: int, body: bytes) -> None:
        self.status_code = status_code
        self.body = body


SecGet = Callable[[str, dict[str, str], float], RawSecResponse]
Clock = Callable[[], datetime]


def _sec_get(url: str, headers: dict[str, str], timeout: float) -> RawSecResponse:
    response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    return RawSecResponse(status_code=response.status_code, body=response.content)


class SecBulkDownloader:
    """Download nightly SEC Company Facts and Submissions archives."""

    source = "sec_edgar"

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        raw_root: Path = Path("data/raw"),
        http_get: SecGet = _sec_get,
        clock: Clock = utc_now,
        timeout: float = 600.0,
    ) -> None:
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", "")
        self.raw_root = raw_root
        self._http_get = http_get
        self._clock = clock
        self.timeout = timeout

    def download(self, archive: str) -> RawSecResponse:
        """Fetch one official bulk archive with the required identity header."""

        if archive not in SEC_ARCHIVES:
            raise ValueError(f"unsupported SEC archive: {archive}")
        if not self.user_agent:
            raise SecConfigurationError(
                "SEC_USER_AGENT must identify an organization and contact email"
            )
        response = self._http_get(
            SEC_ARCHIVES[archive],
            {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"},
            self.timeout,
        )
        self.validate_response(response)
        return response

    def validate_response(self, response: RawSecResponse) -> None:
        if response.status_code != httpx.codes.OK:
            raise InvalidSecResponseError(f"SEC returned HTTP {response.status_code}")
        if not response.body.startswith(b"PK"):
            raise InvalidSecResponseError("SEC response is not a ZIP archive")

    def save_raw(self, response: RawSecResponse, *, archive: str) -> Path:
        """Save the exact bulk ZIP with acquisition metadata."""

        self.validate_response(response)
        downloaded_at = self._clock().astimezone(UTC).isoformat(timespec="seconds")
        return save_snapshot(
            content=response.body,
            metadata=SnapshotMetadata(
                source=self.source,
                downloaded_at=downloaded_at,
                rows=0,
                date_min=None,
                date_max=None,
            ),
            raw_root=self.raw_root,
            category="fundamentals",
            source=self.source,
            stem=archive,
            suffix=".zip",
        )

    def download_and_save(self, archive: str) -> Path:
        return self.save_raw(self.download(archive), archive=archive)
