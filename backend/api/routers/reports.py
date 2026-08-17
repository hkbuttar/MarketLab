"""Research report endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.report import ReportContent, ReportItem
from backend.services.reports import (
    generate_backtest_report,
    report_catalog,
    report_content,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports() -> dict[str, list[ReportItem]]:
    return {"items": report_catalog()}


@router.get("/content", response_model=ReportContent)
def get_report_content(path: Annotated[str, Query(min_length=1)]) -> ReportContent:
    try:
        return report_content(path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="report not found") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/backtests/{experiment_id}", response_model=list[ReportItem])
def create_backtest_report(experiment_id: str) -> list[ReportItem]:
    try:
        return generate_backtest_report(experiment_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="backtest not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
