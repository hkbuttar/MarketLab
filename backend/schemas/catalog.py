"""Shared API response schemas."""

from pydantic import BaseModel, ConfigDict


class CatalogItem(BaseModel):
    """Discoverable quantitative engine capability."""

    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    description: str
