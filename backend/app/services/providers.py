"""Authoritative knowledge-base providers used by the research engine.

Every provider returns a list of `Source` objects and never raises: a provider
outage degrades the report instead of failing the whole request. Status strings
are surfaced to the UI through `HistoricalReport.provider_status`.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from app.config import get_settings
from app.models import Source
from app.services.http import get_client

logger = logging.getLogger(__name__)

ProviderResult = tuple[list[Source], str]

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")


def _extract_year(text: str | None) -> int | None:
    if not text:
        return None
    match = _YEAR_RE.search(text)
    return int(match.group(1)) if match else None


async def fetch_wikipedia(latitude: float, longitude: float, radius_meters: int) -> ProviderResult:
    """Geosearch nearby articles, then pull their intro extracts in one batch."""
    settings = get_settings()
    base_url = settings.wikipedia_base_url
    client = get_client()
    try:
        geo_response = await client.get(
            base_url,
            params={
                "action": "query",
                "format": "json",
                "list": "geosearch",
                "gscoord": f"{latitude}|{longitude}",
                "gsradius": min(max(radius_meters, 10), 10000),
                "gslimit": settings.max_sources_per_provider,
            },
        )
        geo_response.raise_for_status()
        pages = geo_response.json().get("query", {}).get("geosearch", [])
        if not pages:
            return [], "ok: no nearby articles"

        titles = "|".join(page["title"] for page in pages)
        extract_response = await client.get(
            base_url,
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "inprop": "url",
                "titles": titles,
            },
        )
        extract_response.raise_for_status()
        extracts: dict[str, Any] = extract_response.json().get("query", {}).get("pages", {})
        by_title = {page.get("title"): page for page in extracts.values()}

        sources: list[Source] = []
        for page in pages:
            detail = by_title.get(page["title"], {})
            extract = (detail.get("extract") or "").strip()
            sources.append(
                Source(
                    provider="wikipedia",
                    title=page["title"],
                    url=detail.get("fullurl")
                    or f"https://{settings.wikipedia_language}.wikipedia.org/wiki/{page['title'].replace(' ', '_')}",
                    snippet=extract[:1200] or None,
                    year=_extract_year(extract),
                    distance_meters=page.get("dist"),
                )
            )
        return sources, f"ok: {len(sources)} articles"
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Wikipedia provider failed: %s", exc)
        return [], f"error: {type(exc).__name__}"


async def fetch_europeana(place_query: str) -> ProviderResult:
    """Search Europeana cultural heritage records for the resolved place name."""
    settings = get_settings()
    if not settings.europeana_api_key:
        return [], "skipped: EUROPEANA_API_KEY not configured"
    try:
        response = await get_client().get(
            settings.europeana_base_url,
            params={
                "wskey": settings.europeana_api_key,
                "query": place_query,
                "rows": settings.max_sources_per_provider,
                "profile": "standard",
            },
        )
        response.raise_for_status()
        items = response.json().get("items", []) or []
        sources = [
            Source(
                provider="europeana",
                title=_first(item.get("title")) or "Untitled Europeana record",
                url=_first(item.get("guid") or item.get("edmIsShownAt")) or "https://www.europeana.eu",
                snippet=_first(item.get("dcDescriptionLangAware", {}).get("en") if isinstance(item.get("dcDescriptionLangAware"), dict) else None)
                or _first(item.get("dcDescription")),
                year=_extract_year(_first(item.get("year"))),
                creator=_first(item.get("dcCreator")),
            )
            for item in items
        ]
        return sources, f"ok: {len(sources)} records"
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Europeana provider failed: %s", exc)
        return [], f"error: {type(exc).__name__}"


async def fetch_internet_archive(place_label: str, region: str | None = None) -> ProviderResult:
    """Search the Internet Archive full-text catalogue for the place name.

    Only the place label is phrase-matched: adding the administrative region to the
    quoted phrase would make the exact-match query fail for almost every item.
    """
    settings = get_settings()
    query = f'"{place_label}"'
    if region:
        query += f" OR \"{place_label}, {region}\""
    try:
        response = await get_client().get(
            settings.internet_archive_base_url,
            params=[
                ("q", f"({query}) AND (mediatype:texts OR mediatype:image)"),
                ("fl[]", "identifier"),
                ("fl[]", "title"),
                ("fl[]", "year"),
                ("fl[]", "description"),
                ("fl[]", "creator"),
                ("rows", str(settings.max_sources_per_provider)),
                ("page", "1"),
                ("output", "json"),
            ],
        )
        response.raise_for_status()
        docs = response.json().get("response", {}).get("docs", []) or []
        sources = [
            Source(
                provider="internet_archive",
                title=_first(doc.get("title")) or doc.get("identifier", "Archive item"),
                url=f"https://archive.org/details/{doc['identifier']}",
                snippet=_truncate(_first(doc.get("description"))),
                year=_coerce_year(doc.get("year")),
                creator=_first(doc.get("creator")),
            )
            for doc in docs
            if doc.get("identifier")
        ]
        return sources, f"ok: {len(sources)} items"
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Internet Archive provider failed: %s", exc)
        return [], f"error: {type(exc).__name__}"


async def gather_sources(
    latitude: float, longitude: float, place_label: str, region: str | None, radius_meters: int
) -> tuple[list[Source], dict[str, str]]:
    europeana_query = f"{place_label} {region}".strip() if region else place_label
    wikipedia, europeana, archive = await asyncio.gather(
        fetch_wikipedia(latitude, longitude, radius_meters),
        fetch_europeana(europeana_query),
        fetch_internet_archive(place_label, region),
    )
    status = {
        "wikipedia": wikipedia[1],
        "europeana": europeana[1],
        "internet_archive": archive[1],
    }
    return [*wikipedia[0], *europeana[0], *archive[0]], status


def _first(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value)


def _truncate(value: str | None, limit: int = 600) -> str | None:
    if not value:
        return None
    clean = re.sub(r"<[^>]+>", " ", value)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:limit] or None


def _coerce_year(value: Any) -> int | None:
    text = _first(value)
    if not text:
        return None
    return _extract_year(text)
