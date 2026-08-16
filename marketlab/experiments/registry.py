"""Filesystem-backed experiment registry with artifact fingerprints."""

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def record_experiment(
    name: str,
    *,
    command: str,
    parameters: dict[str, Any],
    inputs: list[Path],
    outputs: list[Path],
    metrics: dict[str, Any],
    project_root: Path = Path("."),
    registry_root: Path = Path("experiments"),
) -> Path:
    """Write an immutable manifest for a completed experiment run."""

    if not name or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in name
    ):
        raise ValueError(
            "experiment name must use lowercase letters, digits, '-' or '_'"
        )
    root = project_root.resolve()
    timestamp = datetime.now(UTC)
    run_id = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    manifest = {
        "schema_version": 1,
        "experiment": name,
        "run_id": run_id,
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "command": command,
        "git": _git_state(root),
        "parameters": parameters,
        "inputs": [_artifact(path, root) for path in inputs],
        "outputs": [_artifact(path, root) for path in outputs],
        "metrics": metrics,
    }
    directory = registry_root / name
    if not directory.is_absolute():
        directory = root / directory
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{run_id}.json"
    partial = destination.with_suffix(".json.part")
    partial.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(destination)
    return destination


def _artifact(path: Path, root: Path) -> dict[str, str | int]:
    resolved = path.resolve()
    try:
        display_path = str(resolved.relative_to(root))
    except ValueError as error:
        raise ValueError(f"artifact is outside project root: {path}") from error
    if not resolved.is_file():
        raise FileNotFoundError(f"artifact does not exist: {display_path}")
    digest = hashlib.sha256()
    with resolved.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "path": display_path,
        "size_bytes": resolved.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def _git_state(root: Path) -> dict[str, str | bool | None]:
    revision = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain", "--untracked-files=no")
    return {
        "revision": revision,
        "dirty": bool(status) if status is not None else None,
    }


def _git(root: Path, *arguments: str) -> str | None:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None
