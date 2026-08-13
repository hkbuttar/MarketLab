"""Common contracts and persistence helpers for raw-data downloaders."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, TypeVar

ResponseT = TypeVar("ResponseT")


class Downloader(Protocol[ResponseT]):
    """Conceptual interface shared by all provider adapters."""

    def download(self, *args: object, **kwargs: object) -> ResponseT:
        """Fetch an unmodified response from a provider."""

    def validate_response(self, response: ResponseT) -> None:
        """Reject provider errors or structurally unusable responses."""

    def save_raw(self, response: ResponseT, *args: object, **kwargs: object) -> Path:
        """Persist a provider response without canonical transformation."""


@dataclass(frozen=True, slots=True)
class SnapshotMetadata:
    """Sidecar metadata recorded for every raw snapshot."""

    source: str
    downloaded_at: str
    rows: int
    date_min: str | None
    date_max: str | None


def utc_now() -> datetime:
    """Return the current UTC time; injectable to keep persistence testable."""

    return datetime.now(UTC)


def save_snapshot(
    *,
    content: bytes,
    metadata: SnapshotMetadata,
    raw_root: Path,
    category: str,
    source: str,
    stem: str,
    suffix: str,
) -> Path:
    """Save raw bytes and an adjacent JSON metadata file."""

    snapshot_id = metadata.downloaded_at.replace("+00:00", "Z").replace(":", "")
    snapshot_dir = raw_root / category / source / stem / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    data_path = snapshot_dir / f"{stem}{suffix}"
    data_path.write_bytes(content)
    metadata_path = snapshot_dir / f"{stem}.metadata.json"
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return data_path
