"""Backtest execution and result endpoints."""

from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from backend.schemas.backtest import (
    BacktestAccepted,
    BacktestListItem,
    BacktestRequest,
    BacktestResult,
    BacktestStatus,
)
from backend.services.backtests import (
    create_backtest_job,
    list_backtest_jobs,
    read_backtest_job,
    read_backtest_result,
    run_backtest_job,
)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("")
def list_backtests() -> dict[str, list[BacktestListItem]]:
    return {
        "items": [BacktestListItem.model_validate(job) for job in list_backtest_jobs()]
    }


@router.post("", response_model=BacktestAccepted, status_code=status.HTTP_202_ACCEPTED)
def submit_backtest(
    request: BacktestRequest, background_tasks: BackgroundTasks
) -> BacktestAccepted:
    """Queue a canonical backtest without blocking the API response."""

    experiment_id = str(uuid4())
    create_backtest_job(experiment_id, request)
    background_tasks.add_task(run_backtest_job, experiment_id, request)
    return BacktestAccepted(experiment_id=experiment_id, status="queued")


@router.get("/{experiment_id}", response_model=BacktestStatus)
def get_backtest(experiment_id: str) -> BacktestStatus:
    """Return current state and compact results for one submitted run."""

    try:
        value = read_backtest_job(experiment_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="backtest not found") from error
    return BacktestStatus.model_validate(value)


@router.get("/{experiment_id}/results", response_model=BacktestResult)
def get_backtest_result(experiment_id: str) -> BacktestResult:
    try:
        return BacktestResult.model_validate(read_backtest_result(experiment_id))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="backtest result not found"
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
