"""Backtest API request and status schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BacktestRequest(BaseModel):
    """Supported canonical daily backtest configuration."""

    model_config = ConfigDict(extra="forbid")

    strategy: Literal["momentum", "low_volatility", "quality_value_momentum"]
    start_date: date
    end_date: date
    capital: float = Field(default=1_000_000, gt=0, le=1_000_000_000)
    rebalance: Literal["monthly"] = "monthly"
    weighting: Literal["equal"] = "equal"
    cost_bps: float = Field(default=10.0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "BacktestRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class BacktestAccepted(BaseModel):
    """Asynchronous backtest submission response."""

    experiment_id: str
    status: Literal["queued"]


class BacktestStatus(BaseModel):
    """Persisted backtest job state."""

    experiment_id: str
    status: Literal["queued", "running", "completed", "failed"]
    artifact_path: str | None = None
    summary: dict[str, object] | None = None
    error: str | None = None
