"""Experiment metadata endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
def list_experiments() -> dict[str, list[object]]:
    return {"items": []}
