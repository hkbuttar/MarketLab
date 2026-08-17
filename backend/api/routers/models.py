"""Persisted machine-learning research endpoints."""

from fastapi import APIRouter, HTTPException

from backend.schemas.ml_lab import MLLabResponse
from backend.services.ml_lab import ml_lab_result

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=MLLabResponse)
def get_models() -> MLLabResponse:
    try:
        return ml_lab_result()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503, detail="ML research artifacts are unavailable"
        ) from error
