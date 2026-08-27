"""Historical intelligence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models import HistoricalReport, ResearchRequest
from app.services import research

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=HistoricalReport)
async def research_post(request: ResearchRequest) -> HistoricalReport:
    return await research.research_location(request)


@router.get("", response_model=HistoricalReport)
async def research_get(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    place_name: str | None = None,
    radius_meters: int | None = Query(default=None, ge=100, le=50000),
) -> HistoricalReport:
    return await research.research_location(
        ResearchRequest(latitude=lat, longitude=lon, place_name=place_name, radius_meters=radius_meters)
    )
