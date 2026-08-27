"""Optional LLM refinement of the heuristic report narrative.

When `OPENAI_API_KEY` is present the retrieved sources are summarised by an
OpenAI-compatible chat completion endpoint; otherwise the deterministic
heuristic narrative is used unchanged.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.config import get_settings
from app.models import Source
from app.services.http import get_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an archaeological research analyst. Using only the supplied sources, write a factual "
    "historical narrative for the location, organised by era (Prehistoric, Ancient, Medieval, Industrial, "
    "Modern). Never invent facts that are absent from the sources. Respond as JSON with keys "
    '"narrative" (string, 4-8 sentences) and "rating" (one of "High", "Medium", "Low").'
)


async def refine_narrative(
    place_label: str, sources: list[Source], heuristic_narrative: str
) -> tuple[str, str | None]:
    """Return (narrative, rating_override). Falls back to the heuristic narrative."""
    settings = get_settings()
    if not settings.openai_api_key or not sources:
        return heuristic_narrative, None

    digest = "\n".join(
        f"- [{source.provider}] {source.title}: {(source.snippet or '')[:400]}" for source in sources[:14]
    )
    payload = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Location: {place_label}\n\nSources:\n{digest}"},
        ],
    }
    try:
        response = await get_client().post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        narrative = str(parsed.get("narrative") or "").strip()
        rating = parsed.get("rating")
        if not narrative:
            return heuristic_narrative, None
        return narrative, rating if rating in ("High", "Medium", "Low") else None
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        logger.warning("LLM refinement failed, using heuristic narrative: %s", exc)
        return heuristic_narrative, None
