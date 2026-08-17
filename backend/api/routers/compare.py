"""Cross-experiment comparison endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.comparison import BacktestComparison
from backend.services.comparison import compare_backtests

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
def list_comparisons() -> dict[str, list[object]]:
    return {"items": []}


@router.get("/backtests", response_model=BacktestComparison)
def compare_persisted_backtests(
    experiment_id: Annotated[list[str] | None, Query()] = None,
) -> BacktestComparison:
    try:
        return compare_backtests(experiment_id or [])
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="backtest not found") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
