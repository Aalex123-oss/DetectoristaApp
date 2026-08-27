# API reference

Base URL: `http://127.0.0.1:8000`. Interactive docs at `/docs`.

## `GET /api/health`

```json
{
  "status": "ok",
  "environment": "development",
  "integrations": { "europeana": false, "mapbox": false, "llm_synthesis": false }
}
```

## `GET /api/layers`

Returns the layer catalogue. Each entry:

```json
{
  "id": "esri-hillshade",
  "name": "Esri World Hillshade",
  "group": "lidar",
  "kind": "tile",
  "url": "https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}",
  "attribution": "Esri, USGS, NOAA",
  "description": "Global multi-directional hillshade derived from elevation models.",
  "default_opacity": 0.85,
  "default_visible": false,
  "max_zoom": 18,
  "epoch": null,
  "wms_layers": null,
  "wms_format": null,
  "wms_transparent": null,
  "supports_intensity": true,
  "requires_token": false
}
```

`group` is one of `basemap`, `lidar` (DEM/DSM/hillshade/contours), `historical` (georeferenced maps and
vintage aerial photography) or `overlay`. `kind` is `tile` or `wms`; WMS entries carry `wms_layers`,
`wms_format` and `wms_transparent`.

## `GET /api/layers/epochs`

`[1875, 1915, 1956, 1973, 1981, 2005, 2015, 2020]` - drives the historical timeline slider.

## `GET /api/search?q=<query>&limit=<n>`

Omni-search. Detects raw coordinates (DD / DMS / UTM) and resolves them locally; otherwise geocodes
via Nominatim with Photon fallback.

```json
{
  "query": "Totana",
  "interpretation": "place",
  "coordinate": null,
  "results": [
    {
      "display_name": "Totana, Murcia, Spain",
      "latitude": 37.77,
      "longitude": -1.5,
      "kind": "town",
      "bounding_box": null,
      "source": "nominatim"
    }
  ]
}
```

For coordinate input, `interpretation` is `"coordinate"` and `coordinate` holds the parsed value:

```json
{
  "latitude": 37.7714,
  "longitude": -1.5023,
  "format": "dms",
  "normalized": "37.771400, -1.502300",
  "utm": "30S 631905E 4181508N"
}
```

## `GET /api/search/coordinate?q=<raw>`

Parses a single coordinate string and returns `ParsedCoordinate` (or `422` with the parse error).
Accepted forms include `37.7714, -1.5023`, `37 46 17 N 1 30 08 W`, `30S 631000 4180000`.

## `GET /api/search/formats?lat=&lon=`

`{ "decimal": "37.771400, -1.502300", "dms": "37°46'17.04\"N 1°30'08.28\"W", "utm": "30S 631905E 4181508N" }`
for the analysis-pin readout.

## `GET|POST /api/research`

GET query params: `lat`, `lon`, optional `place_name`, optional `radius_meters` (100 - 50000).
POST JSON body: `latitude`, `longitude`, optional `place_name`, `radius_meters`, `language`.

Response - `HistoricalReport`:

| Field | Description |
| --- | --- |
| `location`, `place_label`, `administrative_context` | Resolved position and reverse-geocoded context |
| `narrative` | Comprehensive historical narrative |
| `era_breakdown[]` | `{ era, summary, evidence_count }` across Prehistoric, Ancient, Medieval, Industrial, Modern |
| `archaeological_potential` | `{ rating: High\|Medium\|Low, score, confidence, markers, rationale }` |
| `timeline[]` | `{ year, label, era, description, source_url }`, chronologically ordered, negative years = BC |
| `sources[]` | `{ provider, title, url, snippet, year, distance_meters, creator }` |
| `synthesis_engine` | `heuristic` or `llm` |
| `provider_status` | Per-provider `ok` / `skipped: ...` / `error: ...` |
| `generated_at`, `cached` | ISO timestamp and cache indicator |

Example:

```bash
curl -s "http://127.0.0.1:8000/api/research?lat=37.7714&lon=-1.5023"
```
