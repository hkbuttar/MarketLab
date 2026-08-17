"""ML Lab response schemas."""

from pydantic import BaseModel, ConfigDict


class FeatureImportance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    permutation_importance: float
    mean_absolute_shap: float
    top_three_year_fraction: float


class MLModelDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    months: int
    mean_rank_ic: float
    positive_ic_fraction: float
    net_cagr: float
    benchmark_cagr: float
    oos_sharpe: float
    maximum_drawdown: float
    average_turnover: float
    annualized_cost_drag: float
    purging_delta_ic: float | None
    top_features: list[FeatureImportance]


class MLLabResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    explainability_method: str
    transaction_cost_bps: float
    models: list[MLModelDiagnostics]
