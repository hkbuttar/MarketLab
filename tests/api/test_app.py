from fastapi.testclient import TestClient

from backend.api.app import app
from marketlab.features.registry import FEATURES

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_feature_catalog_uses_quantitative_registry() -> None:
    response = client.get("/api/v1/features")

    assert response.status_code == 200
    assert len(response.json()) == len(FEATURES)
    assert {item["name"] for item in response.json()} == set(FEATURES)


def test_blueprint_routers_are_mounted() -> None:
    for path in (
        "factors",
        "strategies",
        "backtests",
        "experiments",
        "compare",
        "reports",
    ):
        response = client.get(f"/api/v1/{path}")
        assert response.status_code == 200
        assert response.json() == {"items": []}


def test_openapi_metadata_and_versioned_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "MarketLab API"
    assert document["info"]["version"] == "0.1.0"
    assert "/api/v1/backtests" in document["paths"]
