"""Verification and execution of recorded experiment manifests."""

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from marketlab.experiments.registry import _artifact, _git_state


class ReproductionError(RuntimeError):
    """Raised when an experiment cannot be reproduced safely or exactly."""


def find_manifest(identifier: str, registry_root: Path) -> Path:
    """Resolve a manifest path or a unique run ID within the registry."""

    supplied = Path(identifier)
    if supplied.is_file():
        return supplied.resolve()
    matches = list(registry_root.glob(f"*/{identifier}.json"))
    if not matches:
        raise FileNotFoundError(f"experiment run not found: {identifier}")
    if len(matches) > 1:
        raise ReproductionError(f"experiment run ID is ambiguous: {identifier}")
    return matches[0].resolve()


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and minimally validate an experiment manifest."""

    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "run_id", "command", "git", "inputs", "outputs"}
    missing = required - manifest.keys()
    if missing:
        raise ReproductionError(f"manifest is missing fields: {sorted(missing)}")
    if manifest["schema_version"] != 1:
        raise ReproductionError("unsupported experiment manifest schema")
    return manifest


def verify_artifacts(
    manifest: dict[str, Any], artifact_type: str, project_root: Path
) -> None:
    """Require recorded files to retain their original size and SHA-256 hash."""

    root = project_root.resolve()
    mismatches: list[str] = []
    for expected in manifest[artifact_type]:
        path = root / expected["path"]
        try:
            actual = _artifact(path, root)
        except FileNotFoundError:
            mismatches.append(f"{expected['path']} (missing)")
            continue
        if actual["size_bytes"] != expected["size_bytes"]:
            mismatches.append(f"{expected['path']} (size changed)")
        elif actual["sha256"] != expected["sha256"]:
            mismatches.append(f"{expected['path']} (content changed)")
    if mismatches:
        raise ReproductionError(
            f"{artifact_type} verification failed: " + ", ".join(mismatches)
        )


def verify_code(
    manifest: dict[str, Any], project_root: Path, *, allow_code_change: bool
) -> None:
    """Require the recorded commit and a clean source tree for exact reruns."""

    if allow_code_change:
        return
    recorded = manifest["git"]
    current = _git_state(project_root.resolve())
    if recorded.get("dirty"):
        raise ReproductionError(
            "the original run used an uncommitted working tree; exact code cannot be "
            "reconstructed (use --allow-code-change for a non-exact rerun)"
        )
    if current["dirty"]:
        raise ReproductionError("current working tree is dirty")
    if current["revision"] != recorded.get("revision"):
        raise ReproductionError(
            f"Git revision differs: expected {recorded.get('revision')}, "
            f"found {current['revision']}"
        )


def reproduce(
    manifest: dict[str, Any],
    project_root: Path,
    *,
    verify_only: bool = False,
    allow_code_change: bool = False,
) -> None:
    """Verify inputs, optionally rerun, and verify deterministic outputs."""

    root = project_root.resolve()
    verify_code(manifest, root, allow_code_change=allow_code_change)
    verify_artifacts(manifest, "inputs", root)
    if verify_only:
        return
    arguments = shlex.split(manifest["command"])
    if not arguments or Path(arguments[0]).name not in {"python", "python3"}:
        raise ReproductionError("only recorded Python script commands are supported")
    if len(arguments) < 2:
        raise ReproductionError("recorded Python command has no script")
    script = (root / arguments[1]).resolve()
    try:
        script.relative_to(root)
    except ValueError as error:
        raise ReproductionError("recorded script is outside the project") from error
    if script.suffix != ".py" or not script.is_file():
        raise ReproductionError("recorded Python script is unavailable")
    subprocess.run([sys.executable, str(script), *arguments[2:]], cwd=root, check=True)
    verify_artifacts(manifest, "outputs", root)
