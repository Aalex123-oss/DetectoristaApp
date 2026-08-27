"""Runtime configuration for the Web GIS backend."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Detectorista Web GIS API"
    environment: str = "development"

    # Contact string required by the Nominatim usage policy.
    user_agent: str = "DetectoristaWebGIS/1.0 (contact: gis@example.org)"

    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    photon_base_url: str = "https://photon.komoot.io"
    wikipedia_base_url: str = "https://en.wikipedia.org/w/api.php"
    wikipedia_language: str = "en"
    europeana_base_url: str = "https://api.europeana.eu/record/v2/search.json"
    internet_archive_base_url: str = "https://archive.org/advancedsearch.php"

    europeana_api_key: str | None = None
    mapbox_access_token: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    http_timeout_seconds: float = 20.0
    research_cache_ttl_seconds: int = 900
    max_sources_per_provider: int = 8
    search_radius_meters: int = 10000

    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
