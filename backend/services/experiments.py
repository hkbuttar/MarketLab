"""Read-only discovery of immutable experiment manifests."""

import json
from pathlib import Path
from typing import Any

from backend.schemas.experiment import ExperimentDetail, ExperimentListItem

EXPERIMENT_ROOT = Path("experiments")


def experiment_catalog(project_root: Path = Path(".")) -> list[ExperimentListItem]:
    root = (project_root.resolve() / EXPERIMENT_ROOT).resolve()
    if not root.is_dir():
        return []
    items = []
    for path in root.glob("*/*.json"):
        if path.name.startswith("."):
            continue
        try:
            manifest = _manifest(path)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            OSError,
        ):
            continue
        git = manifest.get("git") or {}
        items.append(
            ExperimentListItem(
                run_id=str(manifest["run_id"]),
                name=str(manifest["experiment"]),
                created_at=str(manifest["created_at"]),
                git_revision=git.get("revision"),
                git_dirty=git.get("dirty"),
                input_count=len(manifest.get("inputs", [])),
                output_count=len(manifest.get("outputs", [])),
            )
        )
    return sorted(items, key=lambda item: item.created_at, reverse=True)


def experiment_detail(run_id: str, project_root: Path = Path(".")) -> ExperimentDetail:
    if not run_id or Path(run_id).name != run_id:
        raise FileNotFoundError(run_id)
    root = (project_root.resolve() / EXPERIMENT_ROOT).resolve()
    matches = list(root.glob(f"*/{run_id}.json"))
    if len(matches) != 1:
        raise FileNotFoundError(run_id)
    manifest = _manifest(matches[0])
    git = manifest.get("git") or {}
    return ExperimentDetail(
        schema_version=manifest["schema_version"],
        run_id=manifest["run_id"],
        name=manifest["experiment"],
        created_at=manifest["created_at"],
        command=manifest["command"],
        git_revision=git.get("revision"),
        git_dirty=git.get("dirty"),
        parameters=manifest.get("parameters", {}),
        metrics=manifest.get("metrics", {}),
        inputs=manifest.get("inputs", []),
        outputs=manifest.get("outputs", []),
    )


def _manifest(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    for field in (
        "schema_version",
        "run_id",
        "experiment",
        "created_at",
        "command",
    ):
        if field not in document:
            raise KeyError(field)
    if document["schema_version"] != 1:
        raise ValueError("unsupported experiment schema")
    return document
