# Architecture

## Overview

```
Browser (Next.js 14 App Router)
  |
  |  WorkspaceShell  -- owns layer state, pins, focus, report state
  |    +- OmniSearch      -> GET /api/search, /api/search/coordinate
  |    +- LayerSidebar    -> GET /api/layers, /api/layers/epochs
  |    +- ComparatorMap   -> two synced Leaflet maps (swipe / split / single)
  |    +- ReportPanel     -> GET|POST /api/research, GET /api/search/formats
  v
FastAPI (backend/app)
  routers/  search, research, layers
  services/ coordinates, geocoding, providers, analysis, llm, research, layers, http
  |
  +-> Nominatim  (fallback: Photon)
  +-> Wikipedia geosearch + extracts
  +-> Europeana  (optional key)
  +-> Internet Archive advanced search
  +-> OpenAI-compatible chat completions (optional)
```

## Frontend

- `components/WorkspaceShell.tsx` is the only stateful container: layer catalogue, per-layer
  `LayerState` (visible / opacity / intensity / ramp), comparator mode, epoch selection, pins,
  active pin, report, focus target.
- `components/ComparatorMap.tsx` creates **two** Leaflet maps and mirrors `move`/`zoom` events with a
  re-entrancy guard, so both panes stay locked together. Raster/WMS layers are built from the backend
  catalogue; intensity and colour ramps are applied as CSS filters on the tile pane (works for any
  raster source without server-side reprocessing). The splitter is a pointer-event driven clip of the
  right pane; `split` mode instead lays the panes out side by side.
- Analysis pins are created on `click` and `contextmenu`, rendered as divIcon markers in **both**
  panes, and immediately trigger `/api/research` plus `/api/search/formats` for DD/DMS/UTM readouts.

## Backend

| Module | Responsibility |
| --- | --- |
| `services/coordinates.py` | Parses Decimal Degrees, DMS and UTM; UTM<->lat/lon maths verified against PROJ (EPSG:326xx); haversine distance; DD/DMS/UTM formatting |
| `services/geocoding.py` | Nominatim forward/reverse geocoding with automatic Photon fallback (datacentre IPs are frequently 403'd by Nominatim) |
| `services/providers.py` | Async Wikipedia geosearch + extracts, Europeana search, Internet Archive advanced search. Each provider returns `(sources, status)` and swallows its own failures |
| `services/analysis.py` | Era classification, timeline extraction, narrative synthesis, archaeological potential scoring |
| `services/llm.py` | Optional OpenAI-compatible narrative refinement; falls back to the heuristic narrative on any error |
| `services/research.py` | Orchestrates the pipeline and caches results for `CACHE_TTL_SECONDS` keyed on coordinates rounded to 4 decimals + radius |
| `services/layers.py` | Curated catalogue of public basemap, relief/LiDAR-derived and historical raster/WMS layers |

## Research pipeline

1. Reverse geocode the pin (Nominatim -> Photon) to obtain a place label and admin context.
2. Fan out to Wikipedia / Europeana / Internet Archive concurrently with `asyncio.gather`.
3. Sort sources by distance (where geotagged) then relevance, and trim per-provider limits.
4. Classify each source's text into eras (Prehistoric, Ancient, Medieval, Industrial, Modern).
5. Extract dated milestones (including BC years) and order them chronologically.
6. Score archaeological potential.
7. Build the heuristic narrative, optionally refine it with an LLM.
8. Return `HistoricalReport` with `provider_status` describing every degradation.

## Archaeological potential scoring

The score is deliberately explicit and auditable rather than a black box. Weighted marker groups
detected in the retrieved corpus:

- Roman / pre-Roman settlement evidence
- Referenced archaeological sites
- Defensive structures (castles, towers, walls)
- Battles and military activity
- Historic routes (Roman roads, cattle tracks, pilgrim ways)
- Religious and funerary complexes (necropolis, hermitages, monasteries)
- Extractive industry (mines, quarries, kilns)
- Abandoned or deserted settlements
- Prehistoric monuments (dolmens, rock art, tumuli)

Plus bounded contributions from era coverage, source count and source proximity. The total maps to
`High` (>= 60), `Medium` (>= 30) or `Low`, and every triggered marker is returned so the rating can be
explained in the UI.
