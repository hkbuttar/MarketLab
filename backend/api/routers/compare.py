"""Cross-experiment comparison endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
def list_comparisons() -> dict[str, list[object]]:
    return {"items": []}
