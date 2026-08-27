# Layer catalogue

All layers are public services requiring no credentials. Defined in `backend/app/services/layers.py`
and served through `GET /api/layers`.

## Basemaps

| id | Source |
| --- | --- |
| `osm` | OpenStreetMap standard tiles |
| `esri-imagery` | Esri World Imagery (modern satellite) |
| `carto-light` | Carto Positron - neutral canvas for overlay work |
| `opentopomap` | OpenTopoMap - contours and topographic styling |

## Relief / LiDAR-derived

| id | Source | Notes |
| --- | --- | --- |
| `esri-hillshade` | Esri World Hillshade | Global multi-directional hillshade |
| `esri-hillshade-dark` | Esri World Hillshade (dark) | Higher contrast for micro-relief |
| `ign-mdt` | Spanish IGN/IDEE elevation WMS | DEM/DSM derived from the national LiDAR (PNOA-LiDAR) coverage |
| `ign-contours` | Spanish IGN/IDEE contour WMS | Vector-derived contour raster |

Colour ramps and intensity are applied client-side as CSS filters over the raster pane, so any
greyscale relief source can be re-styled (`natural`, `grayscale`, `terrain`, `inverted`, `contrast`)
without server-side reprocessing.

## Historical cartography and vintage aerial photography

| id | Epoch | Source |
| --- | --- | --- |
| `mtn50-first-edition` | 1875 | IGN MTN50 first edition |
| `mtn25-first-edition` | 1915 | IGN MTN25 first edition |
| `ams-1956` | 1956 | AMS 1956-1957 American series aerial photography |
| `interministerial-1973` | 1973 | Interministerial flight 1973-1986 |
| `nacional-1981` | 1981 | National flight 1981-1986 |
| `pnoa-2005` | 2005 | PNOA historical orthophoto |
| `pnoa-2015` | 2015 | PNOA historical orthophoto |
| `pnoa-2020` | 2020 | PNOA historical orthophoto |

The epoch slider in the sidebar activates exactly one historical layer and promotes it to the
comparison pane, so a swipe immediately contrasts that epoch against the current basemap or relief
stack.

## Adding a layer

Append a `LayerDefinition` in `backend/app/services/layers.py`; the frontend picks it up on the next
load with no client changes. Use `group="overlay"` and set `epoch` to make it part of the timeline.
