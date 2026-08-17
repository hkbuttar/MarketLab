"""Strategy definition endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies() -> dict[str, list[object]]:
    return {"items": []}
