"""Tests for persisted backtest discovery and result analytics."""

import csv
import json

import pytest
from fastapi.testclient import TestClient

import backend.services.backtests as service
from backend.api.app import app

client = TestClient(app)


def _completed_job(tmp_path):
    statuses = tmp_path / "statuses"
    outputs = tmp_path / "outputs"
    statuses.mkdir()
    outputs.mkdir()
    artifact = outputs / "result.csv"
    with artifact.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                "date",
                "strategy",
                "gross_nav",
                "net_nav",
                "daily_return",
                "benchmark_nav",
                "cumulative_costs",
            ),
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "date": "2024-01-02",
                    "strategy": "momentum",
                    "gross_nav": 101,
                    "net_nav": 100,
                    "daily_return": 0,
                    "benchmark_nav": 100,
                    "cumulative_costs": 1,
                },
                {
                    "date": "2024-01-03",
                    "strategy": "momentum",
                    "gross_nav": 111,
                    "net_nav": 110,
                    "daily_return": 0.1,
                    "benchmark_nav": 105,
                    "cumulative_costs": 1,
                },
            ]
        )
    (statuses / "test-run.json").write_text(
        json.dumps(
            {
                "experiment_id": "test-run",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00+00:00",
                "request": {"strategy": "momentum"},
                "artifact_path": str(artifact),
            }
        )
    )
    return statuses


def test_lists_persisted_backtests(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(service, "STATUS_ROOT", tmp_path / "missing")
    assert service.list_backtest_jobs() == []
    statuses = _completed_job(tmp_path)
    monkeypatch.setattr(service, "STATUS_ROOT", statuses)

    jobs = service.list_backtest_jobs()

    assert jobs[0]["strategy"] == "momentum"


def test_result_endpoint_calculates_metrics_and_curve(tmp_path, monkeypatch) -> None:
    _completed_job(tmp_path)
    monkeypatch.setattr(service, "STATUS_ROOT", tmp_path / "statuses")

    response = client.get("/api/v1/backtests/test-run/results")

    assert response.status_code == 200
    assert response.json()["metrics"]["total_return"] == pytest.approx(0.1)
    assert response.json()["metrics"]["benchmark_return"] == pytest.approx(0.05)
    assert len(response.json()["equity_curve"]) == 2
