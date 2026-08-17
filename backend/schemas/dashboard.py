"""Dashboard aggregation response schemas."""

from pydantic import BaseModel, ConfigDict


class DashboardMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: float


class RecentExperiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    name: str
    created_at: str
    status: str


class RecentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    updated_at: str


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    best_oos_model: str | None
    best_oos_sharpe: float | None
    average_robustness_score: float | None
    factor_research: list[DashboardMetric]
    recent_experiments: list[RecentExperiment]
    recent_reports: list[RecentReport]
