"""Omni-search: place geocoding plus raw coordinate interpretation."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.models import ParsedCoordinate, SearchResponse
from app.services import geocoding
from app.services.coordinates import (
    CoordinateParseError,
    format_decimal,
    format_dms,
    latlon_to_utm,
    parse_coordinate,
)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def omni_search(
    q: str = Query(min_length=1, description="Place name, address, or coordinates (DD, DMS, UTM)"),
    limit: int = Query(default=6, ge=1, le=20),
) -> SearchResponse:
    try:
        coordinate = parse_coordinate(q)
    except CoordinateParseError:
        coordinate = None

    if coordinate is not None:
        return SearchResponse(query=q, interpretation="coordinate", coordinate=coordinate, results=[])

    try:
        results = await geocoding.geocode(q, limit=limit)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding provider unavailable: {exc}") from exc
    return SearchResponse(query=q, interpretation="place", results=results)


@router.get("/coordinate", response_model=ParsedCoordinate)
def parse(q: str = Query(min_length=1)) -> ParsedCoordinate:
    try:
        return parse_coordinate(q)
    except CoordinateParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/formats")
def formats(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)) -> dict[str, str]:
    """All display formats for a pin location."""
    return {
        "decimal": format_decimal(lat, lon),
        "dms": format_dms(lat, lon),
        "utm": latlon_to_utm(lat, lon),
    }
