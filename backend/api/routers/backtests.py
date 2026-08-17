"""Backtest execution and result endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("")
def list_backtests() -> dict[str, list[object]]:
    return {"items": []}
