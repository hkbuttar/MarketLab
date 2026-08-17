"""Research report endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports() -> dict[str, list[object]]:
    return {"items": []}
