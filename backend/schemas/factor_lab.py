"""Factor Lab API response schemas."""

from pydantic import BaseModel, ConfigDict


class DatedValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: str
    value: float


class NamedValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    value: float


class FactorLabResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor: str
    universe: str
    forward_horizon: int
    start_date: str
    end_date: str
    observations: int
    mean_ic: float
    positive_ic_rate: float
    mean_turnover: float | None
    ic_history: list[DatedValue]
    quantile_returns: list[NamedValue]
    correlations: list[NamedValue]
    sector_exposure: list[NamedValue]
    sector_classification_note: str
