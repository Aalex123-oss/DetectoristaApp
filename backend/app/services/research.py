"""Historical intelligence engine: retrieval, synthesis and caching."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.models import HistoricalReport, ResearchRequest
from app.services import analysis, geocoding, llm, providers

logger = logging.getLogger(__name__)

_cache: dict[tuple[float, float, int], tuple[float, HistoricalReport]] = {}
_locks: dict[tuple[float, float, int], asyncio.Lock] = {}


def _cache_key(request: ResearchRequest, radius: int) -> tuple[float, float, int]:
    return (round(request.latitude, 4), round(request.longitude, 4), radius)


async def research_location(request: ResearchRequest) -> HistoricalReport:
    settings = get_settings()
    radius = request.radius_meters or settings.search_radius_meters
    key = _cache_key(request, radius)

    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = _cache.get(key)
        if cached and time.monotonic() - cached[0] < settings.research_cache_ttl_seconds:
            return cached[1].model_copy(update={"cached": True})

        report = await _build_report(request, radius)
        _cache[key] = (time.monotonic(), report)
        return report


async def _build_report(request: ResearchRequest, radius: int) -> HistoricalReport:
    settings = get_settings()
    provider_status: dict[str, str] = {}

    context = None
    try:
        context = await geocoding.reverse_geocode(request.latitude, request.longitude)
        provider_status["geocoder"] = f"ok: {context.source}" if context else "ok: no match"
    except httpx.HTTPError as exc:
        logger.warning("Reverse geocoding failed: %s", exc)
        provider_status["geocoder"] = f"error: {type(exc).__name__}"

    place_label = (
        request.place_name
        or (context.place_name if context else None)
        or (context.display_name.split(",")[0] if context else None)
        or f"{request.latitude:.5f}, {request.longitude:.5f}"
    )
    region = None
    if context:
        region = next(
            (value for value in (context.county, context.state) if value and value not in place_label), None
        )

    sources, statuses = await providers.gather_sources(
        request.latitude, request.longitude, place_label, region, radius
    )
    provider_status.update(statuses)

    sources.sort(key=lambda s: (s.distance_meters if s.distance_meters is not None else 1e9, s.title))
    sources = sources[: settings.max_sources_per_provider * 3]

    era_breakdown = analysis.build_era_breakdown(sources)
    potential = analysis.score_potential(sources, era_breakdown)
    timeline = analysis.build_timeline(sources)
    heuristic_narrative = analysis.build_narrative(place_label, era_breakdown, potential, sources)

    narrative, rating_override = await llm.refine_narrative(place_label, sources, heuristic_narrative)
    engine = "llm" if narrative != heuristic_narrative else "heuristic"
    provider_status["llm"] = "ok" if engine == "llm" else (
        "skipped: OPENAI_API_KEY not configured" if not settings.openai_api_key else "skipped: heuristic used"
    )
    if rating_override and rating_override != potential.rating:
        potential = potential.model_copy(
            update={
                "rating": rating_override,
                "rationale": potential.rationale + f" LLM review adjusted the rating to {rating_override}.",
            }
        )

    return HistoricalReport(
        location={"latitude": request.latitude, "longitude": request.longitude},  # type: ignore[arg-type]
        place_label=place_label,
        administrative_context=context,
        narrative=narrative,
        era_breakdown=era_breakdown,
        archaeological_potential=potential,
        timeline=timeline,
        sources=sources,
        synthesis_engine=engine,  # type: ignore[arg-type]
        provider_status=provider_status,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def clear_cache() -> None:
    _cache.clear()
    _locks.clear()
