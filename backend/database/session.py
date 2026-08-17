"""Database engine construction without import-time connections."""

import os

from sqlalchemy import Engine, create_engine


def database_url() -> str:
    """Return the configured database URL without providing unsafe defaults."""

    value = os.getenv("MARKETLAB_DATABASE_URL")
    if not value:
        raise RuntimeError("MARKETLAB_DATABASE_URL is not configured")
    return value


def create_database_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine; callers control when a connection is opened."""

    return create_engine(url or database_url(), pool_pre_ping=True)
