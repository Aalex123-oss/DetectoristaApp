"""Geocoding and reverse geocoding over OpenStreetMap data.

Nominatim is the primary provider; Photon (also OSM based) is used as a fallback
because Nominatim rate-limits or blocks shared/datacentre IP ranges.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.models import GeocodeResult, ReverseGeocodeResult
from app.services.http import get_client

logger = logging.getLogger(__name__)


async def geocode(query: str, limit: int = 6) -> list[GeocodeResult]:
    try:
        return await _geocode_nominatim(query, limit)
    except httpx.HTTPError as exc:
        logger.warning("Nominatim search failed (%s), falling back to Photon", exc)
        return await _geocode_photon(query, limit)


async def reverse_geocode(latitude: float, longitude: float) -> ReverseGeocodeResult | None:
    try:
        return await _reverse_nominatim(latitude, longitude)
    except httpx.HTTPError as exc:
        logger.warning("Nominatim reverse failed (%s), falling back to Photon", exc)
        return await _reverse_photon(latitude, longitude)


async def _geocode_nominatim(query: str, limit: int) -> list[GeocodeResult]:
    settings = get_settings()
    response = await get_client().get(
        f"{settings.nominatim_base_url}/search",
        params={
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
            "accept-language": settings.wikipedia_language,
        },
    )
    response.raise_for_status()
    payload: list[dict[str, Any]] = response.json()
    results: list[GeocodeResult] = []
    for item in payload:
        bbox = item.get("boundingbox")
        results.append(
            GeocodeResult(
                display_name=item.get("display_name", "Unknown place"),
                latitude=float(item["lat"]),
                longitude=float(item["lon"]),
                kind=item.get("type"),
                bounding_box=[float(value) for value in bbox] if bbox else None,
            )
        )
    return results


async def _reverse_nominatim(latitude: float, longitude: float) -> ReverseGeocodeResult | None:
    settings = get_settings()
    response = await get_client().get(
        f"{settings.nominatim_base_url}/reverse",
        params={
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "zoom": 14,
            "addressdetails": 1,
            "accept-language": settings.wikipedia_language,
        },
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    if "error" in payload:
        return None
    address: dict[str, Any] = payload.get("address", {})
    place_name = (
        address.get("village")
        or address.get("town")
        or address.get("city")
        or address.get("hamlet")
        or address.get("municipality")
        or address.get("suburb")
    )
    return ReverseGeocodeResult(
        display_name=payload.get("display_name", f"{latitude:.5f}, {longitude:.5f}"),
        place_name=place_name,
        county=address.get("county"),
        state=address.get("state"),
        country=address.get("country"),
        country_code=address.get("country_code"),
        osm_type=payload.get("osm_type"),
        source="nominatim",
    )


async def _geocode_photon(query: str, limit: int) -> list[GeocodeResult]:
    settings = get_settings()
    response = await get_client().get(
        f"{settings.photon_base_url}/api",
        params={"q": query, "limit": limit, "lang": settings.wikipedia_language},
    )
    response.raise_for_status()
    results: list[GeocodeResult] = []
    for feature in response.json().get("features", []):
        properties: dict[str, Any] = feature.get("properties", {})
        coordinates = feature.get("geometry", {}).get("coordinates") or []
        if len(coordinates) < 2:
            continue
        extent = properties.get("extent")
        results.append(
            GeocodeResult(
                display_name=_photon_display_name(properties),
                latitude=float(coordinates[1]),
                longitude=float(coordinates[0]),
                kind=properties.get("osm_value") or properties.get("type"),
                # Photon extent is [minLon, maxLat, maxLon, minLat]; Nominatim order is
                # [minLat, maxLat, minLon, maxLon].
                bounding_box=[extent[3], extent[1], extent[0], extent[2]] if extent else None,
                source="photon",
            )
        )
    return results


async def _reverse_photon(latitude: float, longitude: float) -> ReverseGeocodeResult | None:
    settings = get_settings()
    response = await get_client().get(
        f"{settings.photon_base_url}/reverse",
        params={"lat": latitude, "lon": longitude, "lang": settings.wikipedia_language},
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        return None
    properties: dict[str, Any] = features[0].get("properties", {})
    return ReverseGeocodeResult(
        display_name=_photon_display_name(properties),
        place_name=properties.get("city")
        or properties.get("locality")
        or properties.get("town")
        or properties.get("village")
        or properties.get("district")
        or properties.get("name"),
        county=properties.get("county"),
        state=properties.get("state"),
        country=properties.get("country"),
        country_code=(properties.get("countrycode") or "").lower() or None,
        osm_type=properties.get("osm_type"),
        source="photon",
    )


def _photon_display_name(properties: dict[str, Any]) -> str:
    parts = [
        properties.get("name"),
        properties.get("city") or properties.get("locality"),
        properties.get("county"),
        properties.get("state"),
        properties.get("country"),
    ]
    seen: list[str] = []
    for part in parts:
        if part and part not in seen:
            seen.append(str(part))
    return ", ".join(seen) or "Unknown place"
