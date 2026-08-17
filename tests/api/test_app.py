from fastapi.testclient import TestClient

import backend.api.routers.backtests as backtest_router
import backend.services.backtests as backtest_service
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


def test_backtest_submission_returns_trackable_experiment(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(backtest_service, "STATUS_ROOT", tmp_path / "statuses")
    monkeypatch.setattr(backtest_router, "run_backtest_job", lambda *_: None)

    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy": "momentum",
            "start_date": "2018-01-01",
            "end_date": "2020-12-31",
            "capital": 1_000_000,
            "rebalance": "monthly",
            "weighting": "equal",
            "cost_bps": 10,
        },
    )

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["status"] == "queued"
    status_response = client.get(f"/api/v1/backtests/{accepted['experiment_id']}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"


def test_backtest_request_rejects_unsupported_or_reversed_configuration() -> None:
    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy": "momentum",
            "start_date": "2025-01-01",
            "end_date": "2024-01-01",
            "weighting": "inverse_volatility",
        },
    )

    assert response.status_code == 422
