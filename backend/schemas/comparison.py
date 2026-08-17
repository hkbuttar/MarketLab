"""Cross-experiment comparison schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.schemas.backtest import BacktestMetrics


class ComparedBacktest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    strategy: str
    start_date: str
    end_date: str
    configuration: dict[str, Any]
    metrics: BacktestMetrics


class BacktestComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiments: list[ComparedBacktest]
    configuration_warnings: list[str]
