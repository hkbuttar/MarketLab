"""Factor research endpoints."""

from fastapi import APIRouter, status

router = APIRouter(prefix="/factors", tags=["factors"])


@router.get("", status_code=status.HTTP_200_OK)
def list_factor_results() -> dict[str, list[object]]:
    """Return persisted factor results once the factor service is connected."""

    return {"items": []}
