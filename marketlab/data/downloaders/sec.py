"""Streaming SEC EDGAR bulk archive downloader."""

import json
import os
import shutil
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from marketlab.data.downloaders.base import SnapshotMetadata, utc_now

SEC_ARCHIVES = {
    "companyfacts": "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip",
    "submissions": "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
}
DEFAULT_DISK_RESERVE_BYTES = 1_073_741_824


class SecConfigurationError(RuntimeError):
    """Raised when the SEC-required identifying user agent is absent."""


class InvalidSecResponseError(ValueError):
    """Raised when an SEC bulk response is unusable."""


class InsufficientDiskSpaceError(OSError):
    """Raised before streaming when the advertised archive will not fit."""


@dataclass(slots=True)
class RawSecStream:
    """Streaming response abstraction used by the SEC downloader."""

    status_code: int
    headers: Mapping[str, str]
    chunks: Iterable[bytes]


SecStream = Callable[[str, dict[str, str], float], AbstractContextManager[RawSecStream]]
Clock = Callable[[], datetime]


@contextmanager
def _sec_stream(
    url: str, headers: dict[str, str], timeout: float
) -> Iterator[RawSecStream]:
    with httpx.stream(
        "GET",
        url,
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as response:
        yield RawSecStream(
            status_code=response.status_code,
            headers=response.headers,
            chunks=response.iter_bytes(),
        )


class SecBulkDownloader:
    """Stream nightly SEC Company Facts and Submissions archives to disk."""

    source = "sec_edgar"

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        raw_root: Path = Path("data/raw"),
        http_stream: SecStream = _sec_stream,
        clock: Clock = utc_now,
        timeout: float = 600.0,
        disk_reserve_bytes: int = DEFAULT_DISK_RESERVE_BYTES,
    ) -> None:
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", "")
        self.raw_root = raw_root
        self._http_stream = http_stream
        self._clock = clock
        self.timeout = timeout
        self.disk_reserve_bytes = disk_reserve_bytes

    def download(self, archive: str) -> AbstractContextManager[RawSecStream]:
        """Open one official bulk archive as a streaming response."""

        if archive not in SEC_ARCHIVES:
            raise ValueError(f"unsupported SEC archive: {archive}")
        if not self.user_agent:
            raise SecConfigurationError(
                "SEC_USER_AGENT must identify an organization and contact email"
            )
        return self._http_stream(
            SEC_ARCHIVES[archive],
            {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"},
            self.timeout,
        )

    def save_raw(self, response: RawSecStream, *, archive: str) -> Path:
        """Stream an archive to a temporary file and atomically finalize it."""

        self._validate_response_envelope(response)
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self._require_disk_space(response)

        downloaded_at = self._clock().astimezone(UTC).isoformat(timespec="seconds")
        snapshot_id = downloaded_at.replace("+00:00", "Z").replace(":", "")
        snapshot_dir = (
            self.raw_root / "fundamentals" / self.source / archive / snapshot_id
        )
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        final_path = snapshot_dir / f"{archive}.zip"
        partial_path = snapshot_dir / f"{archive}.zip.part"

        prefix = bytearray()
        try:
            with partial_path.open("xb") as file:
                for chunk in response.chunks:
                    if not chunk:
                        continue
                    if len(prefix) < 2:
                        prefix.extend(chunk[: 2 - len(prefix)])
                    file.write(chunk)
            if bytes(prefix) != b"PK":
                raise InvalidSecResponseError("SEC response is not a ZIP archive")
            partial_path.replace(final_path)
            self._write_metadata(snapshot_dir, archive, downloaded_at)
        except BaseException:
            partial_path.unlink(missing_ok=True)
            if not any(snapshot_dir.iterdir()):
                snapshot_dir.rmdir()
            raise
        return final_path

    def download_and_save(self, archive: str) -> Path:
        """Open, stream, validate, and persist one SEC bulk archive."""

        with self.download(archive) as response:
            return self.save_raw(response, archive=archive)

    def _validate_response_envelope(self, response: RawSecStream) -> None:
        if response.status_code != httpx.codes.OK:
            raise InvalidSecResponseError(f"SEC returned HTTP {response.status_code}")

    def _require_disk_space(self, response: RawSecStream) -> None:
        content_length = response.headers.get("content-length")
        if content_length is None:
            return
        try:
            expected_bytes = int(content_length)
        except ValueError as error:
            raise InvalidSecResponseError(
                "SEC returned an invalid Content-Length header"
            ) from error
        free_bytes = shutil.disk_usage(self.raw_root).free
        if expected_bytes + self.disk_reserve_bytes > free_bytes:
            raise InsufficientDiskSpaceError(
                f"SEC archive requires {expected_bytes} bytes with reserve; "
                f"only {free_bytes} bytes are free"
            )

    def _write_metadata(
        self, snapshot_dir: Path, archive: str, downloaded_at: str
    ) -> None:
        metadata = SnapshotMetadata(
            source=self.source,
            downloaded_at=downloaded_at,
            rows=0,
            date_min=None,
            date_max=None,
        )
        metadata_path = snapshot_dir / f"{archive}.metadata.json"
        metadata_path.write_text(
            json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
