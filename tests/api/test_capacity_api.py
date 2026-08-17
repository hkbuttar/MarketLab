"""Tests for the capacity API service and route."""

import json

from fastapi.testclient import TestClient

import backend.api.routers.capacity as capacity_router
from backend.api.app import app
from backend.services.capacity import capacity_report

client = TestClient(app)


def _write_report(tmp_path) -> None:
    path = tmp_path / "reports/validation/capacity.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "generated_at": "2026-08-17T00:00:00+00:00",
                "assumptions": {
                    "maximum_adv_participation": 0.1,
                    "liquidation_days": 1,
                },
                "strategies": {
                    "momentum": {
                        "latest": {
                            "date": "2026-07-31",
                            "maximum_aum": 25_000_000,
                            "binding_symbol": "SMALL",
                        },
                        "historical_minimum_aum": 10_000_000,
                        "observations": 12,
                        "curve": [
                            {
                                "aum": 10_000_000,
                                "maximum_participation": 0.04,
                                "estimated_cost": 1_000,
                                "estimated_cost_bps": 1,
                                "feasible": True,
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_capacity_service_reads_persisted_report(tmp_path) -> None:
    _write_report(tmp_path)

    result = capacity_report(tmp_path)

    assert result.strategies[0].name == "momentum"
    assert result.strategies[0].latest.binding_symbol == "SMALL"


def test_capacity_route_returns_report(tmp_path, monkeypatch) -> None:
    _write_report(tmp_path)
    monkeypatch.setattr(
        capacity_router, "capacity_report", lambda: capacity_report(tmp_path)
    )

    response = client.get("/api/v1/capacity")

    assert response.status_code == 200
    assert response.json()["strategies"][0]["name"] == "momentum"
