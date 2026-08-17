import pytest
from fastapi.testclient import TestClient

from backend.api.app import app

client = TestClient(app)


def test_factor_catalog_lists_persisted_research() -> None:
    response = client.get("/api/v1/factors")

    assert response.status_code == 200
    assert "momentum_12_1" in response.json()["items"]
    assert "gross_profitability" in response.json()["items"]


def test_factor_lab_filters_window_and_returns_all_diagnostics() -> None:
    response = client.get(
        "/api/v1/factors/momentum_12_1",
        params={
            "start_date": "2020-01-01",
            "end_date": "2022-12-31",
            "universe": "investable_us_equities",
            "forward_horizon": 21,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["factor"] == "momentum_12_1"
    assert result["observations"] == 36
    assert result["start_date"] == "2020-01-31"
    assert result["end_date"] == "2022-12-30"
    assert len(result["quantile_returns"]) == 5
    assert result["mean_turnover"] == pytest.approx(0.246, abs=0.001)
    assert result["correlations"]
    assert result["sector_exposure"]
    assert "current Alpha Vantage labels" in result["sector_classification_note"]


def test_factor_lab_rejects_unknown_factor_and_horizon() -> None:
    assert client.get("/api/v1/factors/not_a_factor").status_code == 404
    assert (
        client.get(
            "/api/v1/factors/momentum_12_1", params={"forward_horizon": 63}
        ).status_code
        == 422
    )
