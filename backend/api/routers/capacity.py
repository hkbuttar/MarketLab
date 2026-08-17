"""Strategy capacity endpoint."""

from fastapi import APIRouter, HTTPException

from backend.schemas.capacity import CapacityResponse
from backend.services.capacity import capacity_report

router = APIRouter(prefix="/capacity", tags=["capacity"])


@router.get("", response_model=CapacityResponse)
def get_capacity() -> CapacityResponse:
    try:
        return capacity_report()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503, detail="capacity report has not been generated"
        ) from error
