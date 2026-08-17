"""Read-only aggregation of generated research artifacts for the dashboard."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.schemas.dashboard import (
    DashboardMetric,
    DashboardSummary,
    RecentExperiment,
    RecentReport,
)


def dashboard_summary(project_root: Path = Path(".")) -> DashboardSummary:
    """Build a compact view without recalculating quantitative results."""

    root = project_root.resolve()
    model, sharpe = _best_model(
        _json(root / "reports/ml/comparison/model_strategy_comparison.json")
    )
    robustness = _average_robustness(
        _json(root / "reports/validation/robustness_scores.json")
    )
    factors = _factor_metrics(_json(root / "reports/factors/tear_sheet_summary.json"))
    return DashboardSummary(
        best_oos_model=model,
        best_oos_sharpe=sharpe,
        average_robustness_score=robustness,
        factor_research=factors,
        recent_experiments=_recent_experiments(root / "experiments"),
        recent_reports=_recent_reports(root / "reports"),
    )


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _best_model(report: dict[str, Any]) -> tuple[str | None, float | None]:
    models = {
        name: values
        for name, values in report.get("results", {}).items()
        if values.get("category") == "ml_model"
    }
    if not models:
        return None, None
    name = max(models, key=lambda model: float(models[model]["sharpe"]))
    return name, float(models[name]["sharpe"])


def _average_robustness(report: dict[str, Any]) -> float | None:
    scores = [
        float(values["overall_score"])
        for values in report.get("strategies", {}).values()
    ]
    return sum(scores) / len(scores) if scores else None


def _factor_metrics(report: dict[str, Any]) -> list[DashboardMetric]:
    values = report.get("information_coefficient", {})
    ranked = sorted(
        values.items(), key=lambda item: abs(float(item[1]["mean"])), reverse=True
    )
    return [
        DashboardMetric(name=name, value=float(metrics["mean"]))
        for name, metrics in ranked[:5]
    ]


def _recent_experiments(root: Path) -> list[RecentExperiment]:
    values: list[RecentExperiment] = []
    for path in root.glob("*/*.json"):
        try:
            manifest = _json(path)
            run_id = str(manifest["run_id"])
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        values.append(
            RecentExperiment(
                experiment_id=run_id,
                name=str(manifest.get("experiment", path.parent.name)),
                created_at=str(manifest.get("created_at", "")),
                status="completed",
            )
        )
    return sorted(values, key=lambda value: value.created_at, reverse=True)[:5]


def _recent_reports(root: Path) -> list[RecentReport]:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [
        RecentReport(
            name=path.stem.replace("_", " ").title(),
            path=str(path.relative_to(root.parent)),
            updated_at=datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
        )
        for path in files[:5]
    ]
