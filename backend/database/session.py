"""Database engine construction without import-time connections."""

import os

from sqlalchemy import Engine, create_engine


def database_url() -> str:
    """Return the configured database URL without providing unsafe defaults."""

    value = os.getenv("MARKETLAB_DATABASE_URL")
    if not value:
        raise RuntimeError("MARKETLAB_DATABASE_URL is not configured")
    return normalize_database_url(value)


def normalize_database_url(value: str) -> str:
    """Select the installed psycopg v3 driver for generic Render URLs."""

    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def create_database_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine; callers control when a connection is opened."""

    configured = normalize_database_url(url) if url else database_url()
    return create_engine(configured, pool_pre_ping=True)
