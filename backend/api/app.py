"""FastAPI application assembly for the MarketLab product layer."""

from fastapi import FastAPI

from backend.api.routers import ROUTERS


def create_app() -> FastAPI:
    """Create the API without opening database or data-provider connections."""

    app = FastAPI(
        title="MarketLab API",
        description="Quantitative research and strategy validation API.",
        version="0.1.0",
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in ROUTERS:
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
