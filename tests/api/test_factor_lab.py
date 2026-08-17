import csv
import gzip
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.services.factor_lab import factor_lab_result

client = TestClient(app)


def test_factor_catalog_comes_from_engine_registry() -> None:
    response = client.get("/api/v1/factors")

    assert response.status_code == 200
    assert "momentum_12_1" in response.json()["items"]
    assert "gross_profitability" in response.json()["items"]


def test_factor_lab_filters_fixture_and_returns_all_diagnostics(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    _write_csv(
        reports / "information_coefficients_investable.csv",
        ("date", "factor", "observations", "ic"),
        [
            ("2019-12-31", "momentum_12_1", 100, 0.9),
            ("2020-01-31", "momentum_12_1", 100, 0.1),
            ("2020-02-28", "momentum_12_1", 100, -0.05),
        ],
    )
    _write_csv(
        reports / "top_quantile_turnover.csv",
        ("date", "factor", "top_quantile_turnover"),
        [("2020-01-31", "momentum_12_1", 0.2), ("2020-02-28", "momentum_12_1", 0.3)],
    )
    _write_csv(
        reports / "quantile_returns_investable.csv",
        ("date", "factor", "quantile", "mean_forward_return"),
        [
            ("2020-01-31", "momentum_12_1", quantile, quantile / 100)
            for quantile in range(1, 6)
        ],
    )
    _write_csv(
        reports / "factor_correlations.csv",
        ("factor_a", "factor_b", "months", "mean_correlation"),
        [("momentum_12_1", "volatility_63", 12, -0.2)],
    )
    panel = tmp_path / "panel.csv.gz"
    with gzip.open(panel, "wt", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=("date", "symbol", "momentum_12_1_quantile")
        )
        writer.writeheader()
        writer.writerow(
            {"date": "2020-01-31", "symbol": "AAA", "momentum_12_1_quantile": 5}
        )
    overviews = tmp_path / "overviews"
    overview = overviews / "AAA_overview/2020/AAA_overview.json"
    overview.parent.mkdir(parents=True)
    overview.write_text(
        json.dumps({"Symbol": "AAA", "Sector": "Technology"}), encoding="utf-8"
    )

    result = factor_lab_result(
        "momentum_12_1",
        "2020-01-01",
        "2020-12-31",
        root=reports,
        panel_path=panel,
        overview_root=overviews,
    )

    assert result.observations == 2
    assert result.mean_ic == 0.025
    assert result.mean_turnover == 0.25
    assert len(result.quantile_returns) == 5
    assert result.correlations[0].name == "volatility_63"
    assert result.sector_exposure[0].name == "Technology"


def test_factor_lab_rejects_unknown_factor_and_horizon() -> None:
    assert client.get("/api/v1/factors/not_a_factor").status_code == 404
    assert (
        client.get(
            "/api/v1/factors/momentum_12_1", params={"forward_horizon": 63}
        ).status_code
        == 422
    )


def _write_csv(
    path: Path, columns: tuple[str, ...], rows: list[tuple[object, ...]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)
