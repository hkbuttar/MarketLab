"""FastAPI application assembly for the MarketLab product layer."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import ROUTERS
from marketlab import __version__


def create_app() -> FastAPI:
    """Create the API without opening database or data-provider connections."""

    app = FastAPI(
        title="MarketLab API",
        description="Quantitative research and strategy validation API.",
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in ROUTERS:
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
