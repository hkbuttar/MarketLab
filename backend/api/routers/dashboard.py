"""Research dashboard summary endpoint."""

from fastapi import APIRouter

from backend.schemas.dashboard import DashboardSummary
from backend.services.dashboard import dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def get_dashboard() -> DashboardSummary:
    return dashboard_summary()
