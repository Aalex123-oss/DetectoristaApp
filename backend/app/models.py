"""Pydantic schemas shared by the API routers and services."""

from typing import Literal

from pydantic import BaseModel, Field

PotentialRating = Literal["High", "Medium", "Low"]
Era = Literal["Prehistoric", "Ancient", "Medieval", "Industrial", "Modern"]

ERA_ORDER: tuple[Era, ...] = ("Prehistoric", "Ancient", "Medieval", "Industrial", "Modern")


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ParsedCoordinate(Coordinate):
    format: Literal["decimal", "dms", "utm", "mgrs-like"]
    normalized: str
    utm: str | None = None


class GeocodeResult(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    kind: str | None = None
    bounding_box: list[float] | None = None
    source: str = "nominatim"


class SearchResponse(BaseModel):
    query: str
    interpretation: Literal["coordinate", "place"]
    coordinate: ParsedCoordinate | None = None
    results: list[GeocodeResult] = Field(default_factory=list)


class ReverseGeocodeResult(BaseModel):
    display_name: str
    source: Literal["nominatim", "photon"] = "nominatim"
    place_name: str | None = None
    county: str | None = None
    state: str | None = None
    country: str | None = None
    country_code: str | None = None
    osm_type: str | None = None


class Source(BaseModel):
    provider: Literal["wikipedia", "europeana", "internet_archive", "nominatim", "llm"]
    title: str
    url: str
    snippet: str | None = None
    year: int | None = None
    distance_meters: float | None = None
    creator: str | None = None


class TimelineEntry(BaseModel):
    year: int | None = None
    label: str
    era: Era
    description: str
    source_url: str | None = None


class EraNarrative(BaseModel):
    era: Era
    summary: str
    evidence_count: int


class ArchaeologicalPotential(BaseModel):
    rating: PotentialRating
    score: float = Field(ge=0, le=100)
    confidence: Literal["high", "medium", "low"]
    markers: list[str] = Field(default_factory=list)
    rationale: str


class HistoricalReport(BaseModel):
    location: Coordinate
    place_label: str
    administrative_context: ReverseGeocodeResult | None = None
    narrative: str
    era_breakdown: list[EraNarrative] = Field(default_factory=list)
    archaeological_potential: ArchaeologicalPotential
    timeline: list[TimelineEntry] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    synthesis_engine: Literal["heuristic", "llm"] = "heuristic"
    provider_status: dict[str, str] = Field(default_factory=dict)
    generated_at: str
    cached: bool = False


class ResearchRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    place_name: str | None = None
    radius_meters: int | None = Field(default=None, ge=100, le=50000)
    language: str | None = None


class LayerDefinition(BaseModel):
    id: str
    name: str
    group: Literal["basemap", "lidar", "historical", "overlay"]
    kind: Literal["tile", "wms"]
    url: str
    attribution: str
    description: str
    default_opacity: float = 1.0
    default_visible: bool = False
    max_zoom: int = 19
    epoch: int | None = None
    wms_layers: str | None = None
    wms_format: str | None = None
    wms_transparent: bool | None = None
    supports_intensity: bool = False
    requires_token: bool = False
