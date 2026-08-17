"""Safe preparation of Render's single persistent artifact disk."""

from pathlib import Path

ARTIFACT_DIRECTORIES = ("data", "reports", "experiments")


def prepare_persistent_storage(storage_root: Path, project_root: Path) -> None:
    """Link runtime artifact paths to directories on the persistent disk."""

    storage_root.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_DIRECTORIES:
        source = storage_root / name
        destination = project_root / name
        source.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            if destination.resolve() != source.resolve():
                raise RuntimeError(
                    f"artifact link points outside configured storage: {destination}"
                )
            continue
        if destination.exists():
            raise RuntimeError(
                f"artifact path already exists and will not be replaced: {destination}"
            )
        destination.symlink_to(source, target_is_directory=True)
