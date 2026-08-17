"""Static checks for the local container deployment contract."""

from pathlib import Path


def test_compose_defines_health_gated_product_stack() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    for service in ("postgres:", "backend:", "frontend:"):
        assert service in compose
    assert "condition: service_healthy" in compose
    assert "MARKETLAB_DATABASE_URL" in compose
    assert "./data:/app/data" in compose
    assert "python -m scripts.create_database_schema" in compose


def test_images_do_not_copy_local_research_artifacts() -> None:
    ignored = Path(".dockerignore").read_text(encoding="utf-8").splitlines()

    assert {"data", "experiments", "reports"} <= set(ignored)
    assert Path("docker/backend.Dockerfile").is_file()
    assert Path("docker/frontend.Dockerfile").is_file()
    assert "PYTHONPATH=/app" in Path("docker/backend.Dockerfile").read_text(
        encoding="utf-8"
    )
