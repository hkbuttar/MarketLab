"""Experiment metadata endpoints."""

from fastapi import APIRouter, HTTPException

from backend.schemas.experiment import ExperimentDetail, ExperimentListItem
from backend.services.experiments import experiment_catalog, experiment_detail

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
def list_experiments() -> dict[str, list[ExperimentListItem]]:
    return {"items": experiment_catalog()}


@router.get("/{run_id}", response_model=ExperimentDetail)
def get_experiment(run_id: str) -> ExperimentDetail:
    try:
        return experiment_detail(run_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="experiment not found") from error
