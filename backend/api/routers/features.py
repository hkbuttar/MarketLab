"""Feature discovery endpoints backed by the quantitative registry."""

from fastapi import APIRouter

from backend.schemas.catalog import CatalogItem
from marketlab.features.registry import FEATURES

router = APIRouter(prefix="/features", tags=["features"])


@router.get("", response_model=list[CatalogItem])
def list_features() -> list[CatalogItem]:
    """List registered features without copying definitions into the API."""

    return [
        CatalogItem(
            name=feature.name,
            category=feature.family,
            description=feature.description,
        )
        for feature in sorted(FEATURES.values(), key=lambda value: value.name)
    ]
