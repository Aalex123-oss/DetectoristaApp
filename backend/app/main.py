"""FastAPI application entrypoint for the Detectorista Web GIS backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import layers, research, search
from app.services.http import close_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Spatial services for LiDAR visualisation, historical cartography comparison and "
            "automated archaeological / historical intelligence research."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(search.router)
    app.include_router(research.router)
    app.include_router(layers.router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "integrations": {
                "europeana": bool(settings.europeana_api_key),
                "mapbox": bool(settings.mapbox_access_token),
                "llm_synthesis": bool(settings.openai_api_key),
            },
        }

    return app


app = create_app()
