"""Capacity API response schemas."""

from pydantic import BaseModel, ConfigDict


class CapacityCurvePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aum: float
    maximum_participation: float
    estimated_cost: float
    estimated_cost_bps: float
    feasible: bool


class CapacitySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    maximum_aum: float
    binding_symbol: str


class StrategyCapacity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    latest: CapacitySnapshot
    historical_minimum_aum: float
    observations: int
    curve: list[CapacityCurvePoint]


class CapacityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: str
    maximum_adv_participation: float
    liquidation_days: int
    strategies: list[StrategyCapacity]
