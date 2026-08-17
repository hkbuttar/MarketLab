"""Tests for evidence-based flagship study generation."""

from pathlib import Path

import pytest

from marketlab.reporting.studies import _ml_study, _strategy_conclusion


def test_ml_study_reports_negative_incremental_result() -> None:
    comparison = {
        "constraints": {"cost_bps": 10},
        "results": {
            "SPY": _result("benchmark", 0.14, 0.71, 0.0),
            "quality_value_momentum": _result("simple_strategy", 0.12, 0.52, -0.02),
            "gradient_boosting": _result("ml_model", 0.09, 0.40, -0.05),
            "elastic_net": _result("ml_model", 0.08, 0.38, -0.06),
        },
    }

    study = _ml_study(comparison)

    assert "did not provide incremental" in study.sections["Evidence-based finding"]
    assert "gradient boosting" in study.sections["Simple-strategy comparison"]


def test_momentum_conclusion_discloses_weakness() -> None:
    conclusion = _strategy_conclusion(
        "momentum", {"maximum_drawdown": -0.63}, {"label": "weak"}
    )
    assert "-63.00%" in conclusion
    assert "weak" in conclusion


def test_missing_artifacts_fail_clearly(tmp_path: Path) -> None:
    from marketlab.reporting.studies import generate_flagship_studies

    with pytest.raises(FileNotFoundError, match="required study artifact"):
        generate_flagship_studies(tmp_path)


def _result(
    category: str, cagr: float, sharpe: float, active_cagr: float
) -> dict[str, object]:
    return {
        "category": category,
        "net_cagr": cagr,
        "sharpe": sharpe,
        "active_cagr": active_cagr,
        "start_date": "2018-01-31",
        "end_date": "2026-06-30",
        "months": 102,
    }
