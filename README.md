# Detectorista Web GIS

Professional Web GIS workspace for **LiDAR / relief visualisation**, **historical cartographic comparison** and
**automated historical & archaeological intelligence research**.

```
frontend/   Next.js 14 (App Router, TypeScript, Tailwind) + Leaflet dual-pane comparator
backend/    FastAPI service: geocoding, coordinate maths, async research agents
docs/       Architecture, API reference and layer catalogue
scripts/    setup.sh (provision) and dev.sh (run both services)
```

## Feature map

| Requirement | Where |
| --- | --- |
| LiDAR / DEM / DSM / hillshade raster + WMS layers | `backend/app/services/layers.py`, `frontend/components/ComparatorMap.tsx` |
| Layer sidebar: visibility, opacity, intensity, colour ramp | `frontend/components/LayerSidebar.tsx` |
| Swipe splitter + split-screen comparator with synced pan/zoom | `frontend/components/ComparatorMap.tsx` |
| Historical map archive + epoch timeline slider | `backend/app/services/layers.py` (`historical_epochs`), `LayerSidebar` |
| Omni-search: places, Decimal Degrees, DMS, UTM | `frontend/components/OmniSearch.tsx`, `backend/app/services/coordinates.py` |
| Analysis pins (click / right-click) with DD + DMS + UTM readout | `ComparatorMap`, `ReportPanel` |
| Historical intelligence engine (Wikipedia, Europeana, Internet Archive, optional LLM) | `backend/app/services/{providers,analysis,llm,research}.py` |
| Collapsible Historical Intelligence Report | `frontend/components/ReportPanel.tsx` |

## Quick start

```bash
git clone https://github.com/Aalex123-oss/DetectoristaApp.git
cd DetectoristaApp

# 1. Provision backend venv + frontend packages, seed .env files, run backend tests
bash scripts/setup.sh

# 2. Run FastAPI (:8000) and Next.js (:3000) together
npm run dev
```

Then open <http://localhost:3000>. API docs: <http://127.0.0.1:8000/docs>.

### Manual start

```bash
# Backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (second shell)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Configuration

Copy `.env.example` (root) for a single annotated reference, or use `backend/.env.example` and
`frontend/.env.example` directly. **No key is required** - the stack boots and produces real reports
out of the box.

| Variable | Effect when unset |
| --- | --- |
| `EUROPEANA_API_KEY` | Europeana provider is skipped; Wikipedia + Internet Archive still run |
| `OPENAI_API_KEY` | Narrative is produced by the deterministic heuristic synthesiser instead of an LLM |
| `MAPBOX_ACCESS_TOKEN` | Esri World Imagery is used as the satellite basemap |

Degradation is always reported back in `provider_status` on the report payload and rendered in the UI.

## Verifying the research engine

```bash
curl -s "http://127.0.0.1:8000/api/research?lat=37.7714&lon=-1.5023" | python3 -m json.tool
```

A live run against Totana (Murcia) returns a structured `HistoricalReport`:

```json
{
  "place_label": "Totana",
  "archaeological_potential": {
    "rating": "High",
    "score": 65.6,
    "confidence": "high",
    "markers": ["Roman or pre-Roman settlement evidence", "Defensive structures / fortifications", "..."]
  },
  "era_breakdown": [{ "era": "Medieval", "summary": "...", "evidence_count": 2 }],
  "timeline": [{ "year": 1889, "label": "1889 — Sierra Espuña", "era": "Industrial", "source_url": "https://..." }],
  "sources": [{ "provider": "wikipedia", "title": "...", "url": "https://..." }],
  "synthesis_engine": "heuristic",
  "provider_status": {
    "geocoder": "ok: photon",
    "wikipedia": "ok: 4 articles",
    "europeana": "skipped: EUROPEANA_API_KEY not configured",
    "internet_archive": "ok: 8 items",
    "llm": "skipped: OPENAI_API_KEY not configured"
  }
}
```

## Tests & checks

```bash
cd backend && .venv/bin/pytest -q     # 21 tests: coordinates, scoring, API, provider fallbacks
npm run typecheck                     # frontend tsc --noEmit
npm run lint                          # next lint
npm run build                         # production build
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - request flow, module responsibilities, scoring model
- [`docs/API.md`](docs/API.md) - endpoint reference and payload shapes
- [`docs/LAYERS.md`](docs/LAYERS.md) - LiDAR / relief / historical layer catalogue and sources

## Legacy Streamlit app

`app_detectorista.py` (Totana legal/environmental status checker) is untouched and still runs with
`streamlit run app_detectorista.py` after `pip install -r requirements.txt`.
