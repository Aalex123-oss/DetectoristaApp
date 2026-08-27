from app.models import Source
from app.services import analysis


def make_source(title: str, snippet: str, distance: float | None = None, year: int | None = None) -> Source:
    return Source(
        provider="wikipedia",
        title=title,
        url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        snippet=snippet,
        distance_meters=distance,
        year=year,
    )


RICH_SOURCES = [
    make_source(
        "Roman villa of Los Cipreses",
        "The archaeological site contains a Roman villa rustica excavated in 1984. Amphora fragments "
        "and a necropolis were documented near the ancient road.",
        distance=210,
    ),
    make_source(
        "Castillo de Totana",
        "A medieval fortress and watchtower built in the 13th century during al-Andalus rule; the castle "
        "was besieged in 1488 during the Reconquista.",
        distance=980,
    ),
    make_source(
        "Sierra Espuña mines",
        "Industrial mining and a foundry operated from 1875, served by a narrow gauge railway until 1936.",
        distance=3400,
    ),
]

SPARSE_SOURCES = [make_source("Modern reservoir", "A water reservoir completed in 2009.", distance=8000)]


def test_era_breakdown_covers_multiple_eras():
    breakdown = analysis.build_era_breakdown(RICH_SOURCES)
    eras = {entry.era for entry in breakdown}
    assert {"Ancient", "Medieval", "Industrial"} <= eras
    assert all(entry.evidence_count >= 1 for entry in breakdown)


def test_high_potential_for_rich_sources():
    breakdown = analysis.build_era_breakdown(RICH_SOURCES)
    potential = analysis.score_potential(RICH_SOURCES, breakdown)
    assert potential.rating == "High"
    assert potential.score >= 60
    assert "Recorded archaeological site" in potential.markers


def test_low_potential_for_sparse_sources():
    breakdown = analysis.build_era_breakdown(SPARSE_SOURCES)
    potential = analysis.score_potential(SPARSE_SOURCES, breakdown)
    assert potential.rating == "Low"
    assert potential.confidence == "low"


def test_timeline_is_chronologically_sorted_with_bc_support():
    sources = RICH_SOURCES + [make_source("Iberian oppidum", "The hilltop settlement was founded in 400 BC.")]
    timeline = analysis.build_timeline(sources)
    years = [entry.year for entry in timeline if entry.year is not None]
    assert years == sorted(years)
    assert years[0] == -400
    assert any(entry.era == "Medieval" for entry in timeline)


def test_narrative_mentions_rating_and_place():
    breakdown = analysis.build_era_breakdown(RICH_SOURCES)
    potential = analysis.score_potential(RICH_SOURCES, breakdown)
    narrative = analysis.build_narrative("Totana", breakdown, potential, RICH_SOURCES)
    assert "Totana" in narrative
    assert potential.rating in narrative


def test_era_for_year_boundaries():
    assert analysis.era_for_year(-800) == "Prehistoric"
    assert analysis.era_for_year(100) == "Ancient"
    assert analysis.era_for_year(1200) == "Medieval"
    assert analysis.era_for_year(1850) == "Industrial"
    assert analysis.era_for_year(1990) == "Modern"
