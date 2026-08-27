"""Deterministic synthesis of raw sources into a structured historical report.

The heuristics here are intentionally explicit and auditable: era assignment,
timeline extraction and the archaeological potential score are all derived from
weighted historical markers found in the retrieved source material.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from app.models import (
    ERA_ORDER,
    ArchaeologicalPotential,
    Era,
    EraNarrative,
    Source,
    TimelineEntry,
)

ERA_KEYWORDS: dict[Era, tuple[str, ...]] = {
    "Prehistoric": (
        "prehistoric",
        "palaeolithic",
        "paleolithic",
        "mesolithic",
        "neolithic",
        "bronze age",
        "iron age",
        "megalith",
        "dolmen",
        "tumulus",
        "barrow",
        "rock art",
        "cave painting",
    ),
    "Ancient": (
        "roman",
        "romano",
        "iberian",
        "phoenician",
        "carthaginian",
        "greek",
        "hellenistic",
        "antiquity",
        "villa rustica",
        "aqueduct",
        "amphora",
        "legion",
        "via augusta",
        "necropolis",
    ),
    "Medieval": (
        "medieval",
        "middle ages",
        "moorish",
        "al-andalus",
        "andalusi",
        "visigoth",
        "castle",
        "alcazaba",
        "fortress",
        "monastery",
        "abbey",
        "reconquista",
        "watchtower",
        "hermitage",
    ),
    "Industrial": (
        "industrial",
        "19th century",
        "nineteenth century",
        "mine",
        "mining",
        "foundry",
        "railway",
        "narrow gauge",
        "factory",
        "mill",
        "canal",
        "steam",
        "quarry",
    ),
    "Modern": (
        "20th century",
        "twentieth century",
        "civil war",
        "world war",
        "bunker",
        "airfield",
        "reservoir",
        "urbanisation",
        "urbanization",
        "modern",
        "contemporary",
    ),
}

# Weighted markers that increase the likelihood of finds / buried structures.
POTENTIAL_MARKERS: dict[str, tuple[str, ...]] = {
    "Roman or pre-Roman settlement evidence": (
        "roman",
        "iberian",
        "phoenician",
        "villa",
        "necropolis",
        "amphora",
    ),
    "Recorded archaeological site": (
        "archaeological site",
        "excavation",
        "archaeological",
        "yacimiento",
        "artefact",
        "artifact",
        "hoard",
    ),
    "Defensive structures / fortifications": (
        "castle",
        "fortress",
        "alcazaba",
        "watchtower",
        "citadel",
        "rampart",
        "bunker",
    ),
    "Battles or military activity": ("battle", "siege", "skirmish", "war", "conquest"),
    "Historic routes and crossings": (
        "road",
        "via ",
        "route",
        "ford",
        "bridge",
        "cañada",
        "drovers",
        "pilgrimage",
    ),
    "Religious or funerary complexes": (
        "monastery",
        "abbey",
        "hermitage",
        "church",
        "mosque",
        "cemetery",
        "burial",
        "tomb",
    ),
    "Extractive industry heritage": ("mine", "mining", "quarry", "foundry", "smelting", "slag"),
    "Abandoned or deserted settlement": (
        "abandoned",
        "deserted",
        "ruins",
        "ruined",
        "despoblado",
        "ghost town",
    ),
    "Prehistoric monuments": ("dolmen", "megalith", "tumulus", "barrow", "cave painting", "rock art"),
}

MARKER_WEIGHTS: dict[str, float] = {
    "Roman or pre-Roman settlement evidence": 16,
    "Recorded archaeological site": 20,
    "Defensive structures / fortifications": 12,
    "Battles or military activity": 10,
    "Historic routes and crossings": 7,
    "Religious or funerary complexes": 9,
    "Extractive industry heritage": 6,
    "Abandoned or deserted settlement": 11,
    "Prehistoric monuments": 15,
}

CENTURY_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)[- ]century\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:in|since|from|by|during)?\s?((?:1[0-9]{3}|20[0-2][0-9]))\b")
BC_RE = re.compile(r"\b(\d{1,4})\s?(?:BC|BCE)\b", re.IGNORECASE)


def _source_text(source: Source) -> str:
    return " ".join(filter(None, [source.title, source.snippet])).lower()


def classify_eras(sources: Iterable[Source]) -> dict[Era, list[Source]]:
    buckets: dict[Era, list[Source]] = defaultdict(list)
    for source in sources:
        text = _source_text(source)
        matched = False
        for era, keywords in ERA_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                buckets[era].append(source)
                matched = True
        if not matched and source.year:
            buckets[era_for_year(source.year)].append(source)
    return buckets


def era_for_year(year: int) -> Era:
    if year < -500:
        return "Prehistoric"
    if year < 500:
        return "Ancient"
    if year < 1500:
        return "Medieval"
    if year < 1900:
        return "Industrial"
    return "Modern"


def build_era_breakdown(sources: list[Source]) -> list[EraNarrative]:
    buckets = classify_eras(sources)
    breakdown: list[EraNarrative] = []
    for era in ERA_ORDER:
        era_sources = buckets.get(era, [])
        if not era_sources:
            continue
        highlights = [s.title for s in era_sources[:4]]
        excerpt = next((s.snippet for s in era_sources if s.snippet), None)
        summary = f"{len(era_sources)} source(s) reference the {era.lower()} period near this location: " + ", ".join(
            highlights
        )
        if excerpt:
            summary += f". Representative account: {excerpt[:320].rstrip()}…"
        breakdown.append(EraNarrative(era=era, summary=summary, evidence_count=len(era_sources)))
    return breakdown


def build_timeline(sources: list[Source], limit: int = 18) -> list[TimelineEntry]:
    entries: dict[tuple[int | None, str], TimelineEntry] = {}
    for source in sources:
        text = " ".join(filter(None, [source.title, source.snippet]))
        contributed = False
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            year = _sentence_year(sentence)
            if year is None:
                continue
            label = sentence.strip()
            if len(label) < 12:
                continue
            contributed = True
            key = (year, label[:60])
            entries.setdefault(
                key,
                TimelineEntry(
                    year=year,
                    label=f"{year if year > 0 else f'{abs(year)} BC'} — {source.title}",
                    era=era_for_year(year),
                    description=label[:400],
                    source_url=source.url,
                ),
            )
        if not contributed and source.year:
            entries.setdefault(
                (source.year, source.title[:60]),
                TimelineEntry(
                    year=source.year,
                    label=f"{source.year} — {source.title}",
                    era=era_for_year(source.year),
                    description=(source.snippet or source.title)[:400],
                    source_url=source.url,
                ),
            )
    ordered = sorted(entries.values(), key=lambda entry: (entry.year is None, entry.year or 0))
    return ordered[:limit]


def _sentence_year(sentence: str) -> int | None:
    bc = BC_RE.search(sentence)
    if bc:
        return -int(bc.group(1))
    year = YEAR_RE.search(sentence)
    if year:
        return int(year.group(1))
    century = CENTURY_RE.search(sentence)
    if century:
        return (int(century.group(1)) - 1) * 100 + 50
    return None


def score_potential(sources: list[Source], eras: list[EraNarrative]) -> ArchaeologicalPotential:
    corpus = " ".join(_source_text(source) for source in sources)
    matched: list[str] = []
    score = 0.0
    for marker, keywords in POTENTIAL_MARKERS.items():
        hits = sum(corpus.count(keyword) for keyword in keywords)
        if hits:
            matched.append(marker)
            # Diminishing returns: repeated mentions add less than the first hit.
            score += MARKER_WEIGHTS[marker] * min(1.0, 0.6 + 0.2 * min(hits, 3))

    # Deep chronological continuity is itself a strong predictor.
    score += 4.0 * len(eras)
    # Density of independent evidence.
    score += min(10.0, len(sources) * 0.8)

    proximity = [s.distance_meters for s in sources if s.distance_meters is not None]
    if proximity and min(proximity) < 500:
        score += 6.0

    score = max(0.0, min(100.0, score))
    rating = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
    confidence = "high" if len(sources) >= 8 else "medium" if len(sources) >= 3 else "low"

    if matched:
        rationale = (
            f"Score {score:.0f}/100 derived from {len(matched)} historical marker group(s) "
            f"({', '.join(matched[:4])}{'…' if len(matched) > 4 else ''}), "
            f"{len(eras)} distinct era(s) of documented occupation and {len(sources)} independent source(s)."
        )
    else:
        rationale = (
            f"Score {score:.0f}/100. No settlement, route, fortification or excavation markers were found in "
            f"{len(sources)} retrieved source(s); the location reads as historically undocumented terrain."
        )
    return ArchaeologicalPotential(
        rating=rating,  # type: ignore[arg-type]
        score=round(score, 1),
        confidence=confidence,  # type: ignore[arg-type]
        markers=matched,
        rationale=rationale,
    )


def build_narrative(place_label: str, eras: list[EraNarrative], potential: ArchaeologicalPotential, sources: list[Source]) -> str:
    if not sources:
        return (
            f"No authoritative records were retrieved for {place_label}. The area is either sparsely documented "
            "or falls outside the coverage of the queried knowledge bases; widen the search radius or query the "
            "nearest named settlement instead."
        )
    provider_names = {
        "wikipedia": "Wikipedia",
        "europeana": "Europeana",
        "internet_archive": "the Internet Archive",
        "nominatim": "OpenStreetMap",
        "llm": "language-model synthesis",
    }
    used = [provider_names[name] for name in provider_names if any(s.provider == name for s in sources)]
    corpus = ", ".join(used[:-1]) + f" and {used[-1]}" if len(used) > 1 else used[0]
    paragraphs = [
        f"{place_label} is documented across {len(eras) or 1} historical era(s) by {len(sources)} retrieved "
        f"source(s) from {corpus}."
    ]
    for era in eras:
        paragraphs.append(era.summary)
    paragraphs.append(
        f"Archaeological potential is rated {potential.rating} ({potential.score:.0f}/100, "
        f"{potential.confidence} confidence). {potential.rationale}"
    )
    return "\n\n".join(paragraphs)
