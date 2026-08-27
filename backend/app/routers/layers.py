"""Layer catalogue endpoints consumed by the frontend layer manager."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import LayerDefinition
from app.services import layers as layer_service

router = APIRouter(prefix="/api/layers", tags=["layers"])


@router.get("", response_model=list[LayerDefinition])
def list_layers() -> list[LayerDefinition]:
    return layer_service.list_layers()


@router.get("/epochs", response_model=list[int])
def list_epochs() -> list[int]:
    return layer_service.historical_epochs()
