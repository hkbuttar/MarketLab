"""Factor research endpoints."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from backend.schemas.factor_lab import FactorLabResult
from backend.services.factor_lab import available_factors, factor_lab_result

router = APIRouter(prefix="/factors", tags=["factors"])


@router.get("", status_code=status.HTTP_200_OK)
def list_factor_results() -> dict[str, list[object]]:
    """List factors with persisted investable-universe research."""

    return {"items": available_factors()}


@router.get("/{factor}", response_model=FactorLabResult)
def get_factor_result(
    factor: str,
    start_date: date = date(2000, 1, 1),
    end_date: date = date(2100, 1, 1),
    universe: Literal["investable_us_equities"] = "investable_us_equities",
    forward_horizon: int = 21,
) -> FactorLabResult:
    """Return consistent Factor Lab diagnostics for one configuration."""

    del universe
    if forward_horizon != 21:
        raise HTTPException(
            status_code=422, detail="only the 21-session horizon is available"
        )
    try:
        return factor_lab_result(factor, start_date.isoformat(), end_date.isoformat())
    except KeyError as error:
        raise HTTPException(status_code=404, detail="factor not found") from error
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503, detail="factor research artifacts are unavailable"
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
