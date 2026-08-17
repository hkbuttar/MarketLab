"""Tests for Render Blueprint runtime support."""

from pathlib import Path

import pytest

from backend.api.app import LOCAL_ORIGINS, allowed_origins
from backend.database.session import normalize_database_url
from marketlab.deployment.render import prepare_persistent_storage
from scripts.start_render import uvicorn_command


def test_render_database_url_uses_installed_psycopg_driver() -> None:
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    configured = "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url(configured) == configured


def test_cors_origins_use_environment_without_wildcards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MARKETLAB_ALLOWED_ORIGINS",
        "https://marketlab.vercel.app/, https://research.example.com",
    )
    assert allowed_origins() == [
        "https://marketlab.vercel.app",
        "https://research.example.com",
    ]
    monkeypatch.delenv("MARKETLAB_ALLOWED_ORIGINS")
    assert allowed_origins() == list(LOCAL_ORIGINS)


def test_storage_preparation_is_resumable(tmp_path: Path) -> None:
    storage = tmp_path / "persistent"
    project = tmp_path / "app"
    project.mkdir()

    prepare_persistent_storage(storage, project)
    prepare_persistent_storage(storage, project)

    for name in ("data", "reports", "experiments"):
        assert (project / name).is_symlink()
        assert (project / name).resolve() == (storage / name).resolve()


def test_storage_preparation_does_not_replace_existing_data(tmp_path: Path) -> None:
    storage = tmp_path / "persistent"
    project = tmp_path / "app"
    (project / "data").mkdir(parents=True)

    with pytest.raises(RuntimeError, match="will not be replaced"):
        prepare_persistent_storage(storage, project)


def test_blueprint_provisions_database_disk_and_secret_prompts() -> None:
    blueprint = Path("render.yaml").read_text(encoding="utf-8")
    assert "runtime: docker" in blueprint
    assert "dockerCommand: python -m scripts.start_render" in blueprint
    assert "healthCheckPath: /health" in blueprint
    assert "mountPath: /app/storage" in blueprint
    assert "property: connectionString" in blueprint
    assert "MARKETLAB_ALLOWED_ORIGINS" in blueprint
    assert blueprint.count("sync: false") == 3


def test_render_start_command_validates_assigned_port() -> None:
    assert uvicorn_command("12000")[-1] == "12000"
    assert uvicorn_command(None)[-1] == "10000"
    with pytest.raises(RuntimeError, match="integer"):
        uvicorn_command("not-a-port")
    with pytest.raises(RuntimeError, match="between"):
        uvicorn_command("70000")
