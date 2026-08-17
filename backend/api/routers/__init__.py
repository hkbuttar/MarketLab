"""Versioned API router registry."""

from fastapi import APIRouter

from backend.api.routers.backtests import router as backtests_router
from backend.api.routers.compare import router as compare_router
from backend.api.routers.dashboard import router as dashboard_router
from backend.api.routers.experiments import router as experiments_router
from backend.api.routers.factors import router as factors_router
from backend.api.routers.features import router as features_router
from backend.api.routers.reports import router as reports_router
from backend.api.routers.strategies import router as strategies_router

ROUTERS: tuple[APIRouter, ...] = (
    dashboard_router,
    features_router,
    factors_router,
    strategies_router,
    backtests_router,
    experiments_router,
    compare_router,
    reports_router,
)

__all__ = ["ROUTERS"]
