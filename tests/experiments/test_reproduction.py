import hashlib
import json
from pathlib import Path

import pytest

from marketlab.experiments.reproduction import (
    ReproductionError,
    find_manifest,
    load_manifest,
    verify_artifacts,
)


def _manifest(path: Path, content: bytes) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "command": "python scripts/run.py",
        "git": {"revision": "a" * 40, "dirty": False},
        "inputs": [
            {
                "path": str(path),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        ],
        "outputs": [],
    }


def test_finds_and_loads_run_by_id(tmp_path: Path) -> None:
    directory = tmp_path / "comparison"
    directory.mkdir()
    path = directory / "run-1.json"
    path.write_text(json.dumps(_manifest(Path("input.csv"), b"data")), encoding="utf-8")

    found = find_manifest("run-1", tmp_path)

    assert found == path
    assert load_manifest(found)["run_id"] == "run-1"


def test_artifact_verification_detects_content_change(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_bytes(b"data")
    manifest = _manifest(Path("input.csv"), b"data")
    verify_artifacts(manifest, "inputs", tmp_path)

    source.write_bytes(b"edit")

    with pytest.raises(ReproductionError, match="content changed"):
        verify_artifacts(manifest, "inputs", tmp_path)


def test_manifest_requires_reproduction_fields(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text('{"schema_version": 1}', encoding="utf-8")

    with pytest.raises(ReproductionError, match="missing fields"):
        load_manifest(path)
