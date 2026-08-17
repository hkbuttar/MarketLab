"""Package-level scaffold checks."""

import json
import tomllib
from pathlib import Path


def test_marketlab_import() -> None:
    import marketlab

    assert marketlab.__version__ == "1.0.0"


def test_release_versions_are_consistent() -> None:
    import marketlab

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    frontend = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads(Path("frontend/package-lock.json").read_text(encoding="utf-8"))

    assert project["project"]["version"] == marketlab.__version__
    assert frontend["version"] == marketlab.__version__
    assert lock["version"] == marketlab.__version__
    assert lock["packages"][""]["version"] == marketlab.__version__
