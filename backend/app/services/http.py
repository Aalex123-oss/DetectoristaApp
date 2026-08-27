"""Shared async HTTP client with sane defaults for third-party APIs."""

from __future__ import annotations

import httpx

from app.config import get_settings

_client: httpx.AsyncClient | None = None


def build_client() -> httpx.AsyncClient:
    settings = get_settings()
    return httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        headers={"User-Agent": settings.user_agent, "Accept": "application/json"},
        follow_redirects=True,
    )


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = build_client()
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
