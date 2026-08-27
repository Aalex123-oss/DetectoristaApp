"""Catalogue of basemaps, LiDAR/terrain products and georeferenced historical maps.

Endpoints were verified against the published capabilities documents of the
Spanish IGN/IDEE WMS services and the ArcGIS Online tile services.
"""

from __future__ import annotations

from app.config import get_settings
from app.models import LayerDefinition

IGN_HISTORIC_ORTHO_WMS = "https://www.ign.es/wms/pnoa-historico"
IGN_FIRST_EDITION_WMS = "https://www.ign.es/wms/primera-edicion-mtn"
IDEE_MDT_WMS = "https://servicios.idee.es/wms-inspire/mdt"

_LAYERS: list[LayerDefinition] = [
    # ---------------------------------------------------------------- basemaps
    LayerDefinition(
        id="osm",
        name="OpenStreetMap",
        group="basemap",
        kind="tile",
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution="© OpenStreetMap contributors",
        description="Standard OSM cartography, useful for orientation and toponymy.",
        default_visible=True,
        max_zoom=19,
    ),
    LayerDefinition(
        id="esri-imagery",
        name="Esri World Imagery (satellite)",
        group="basemap",
        kind="tile",
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri, Maxar, Earthstar Geographics",
        description="High resolution modern satellite imagery; default right-hand pane of the comparator.",
        max_zoom=19,
    ),
    LayerDefinition(
        id="carto-light",
        name="Carto Positron (minimal)",
        group="basemap",
        kind="tile",
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attribution="© OpenStreetMap contributors, © CARTO",
        description="Low-contrast basemap that keeps LiDAR relief readable underneath labels.",
        max_zoom=20,
    ),
    LayerDefinition(
        id="opentopomap",
        name="OpenTopoMap",
        group="basemap",
        kind="tile",
        url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attribution="© OpenTopoMap (CC-BY-SA), SRTM",
        description="Topographic cartography with contour lines and relief shading.",
        max_zoom=17,
    ),
    # ------------------------------------------------------------ LiDAR/terrain
    LayerDefinition(
        id="esri-hillshade",
        name="Global hillshade (DSM derived)",
        group="lidar",
        kind="tile",
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri, Airbus DS, USGS, NGA, NASA, CGIAR",
        description="Multi-directional hillshade of the global elevation surface; ideal for spotting earthworks.",
        default_opacity=0.85,
        default_visible=True,
        supports_intensity=True,
        max_zoom=19,
    ),
    LayerDefinition(
        id="esri-hillshade-dark",
        name="Dark hillshade (relief intensity)",
        group="lidar",
        kind="tile",
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade_Dark/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri, Airbus DS, USGS, NGA, NASA, CGIAR",
        description="Inverted hillshade emphasising micro-relief such as ditches and terraces.",
        default_opacity=0.7,
        supports_intensity=True,
        max_zoom=19,
    ),
    LayerDefinition(
        id="ign-mdt",
        name="IGN LiDAR DEM (Elevaciones)",
        group="lidar",
        kind="wms",
        url=IDEE_MDT_WMS,
        wms_layers="Elevaciones",
        wms_format="image/png",
        wms_transparent=True,
        attribution="Instituto Geográfico Nacional de España (IDEE)",
        description="INSPIRE elevation grid coverage derived from the PNOA LiDAR campaigns (Spain).",
        default_opacity=0.65,
        supports_intensity=True,
        max_zoom=18,
    ),
    LayerDefinition(
        id="ign-contours",
        name="IGN contour lines",
        group="overlay",
        kind="wms",
        url=IDEE_MDT_WMS,
        wms_layers="curvasnivel",
        wms_format="image/png",
        wms_transparent=True,
        attribution="Instituto Geográfico Nacional de España (IDEE)",
        description="Vector contour lines to quantify relief detected on the LiDAR surface.",
        default_opacity=0.8,
        max_zoom=18,
    ),
    # ------------------------------------------------------ historical archive
    LayerDefinition(
        id="mtn50-first-edition",
        name="MTN50 first edition (1875-1968)",
        group="historical",
        kind="wms",
        url=IGN_FIRST_EDITION_WMS,
        wms_layers="MTN50",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN — Primera edición del Mapa Topográfico Nacional",
        description="Georeferenced sheets of the first edition national topographic map at 1:50,000.",
        default_opacity=0.75,
        epoch=1875,
        max_zoom=18,
    ),
    LayerDefinition(
        id="mtn25-first-edition",
        name="MTN25 first edition (1915-1960)",
        group="historical",
        kind="wms",
        url=IGN_FIRST_EDITION_WMS,
        wms_layers="MTN25",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN — Primera edición del Mapa Topográfico Nacional",
        description="First edition 1:25,000 sheets: records field boundaries, mills, roads and ruins.",
        default_opacity=0.75,
        epoch=1915,
        max_zoom=18,
    ),
    LayerDefinition(
        id="ams-1956",
        name="American series aerial (1956-1957)",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="AMS_1956-1957",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN / US Army Map Service historical orthophotography",
        description="Vintage aerial photography flown before modern urban expansion.",
        default_opacity=0.9,
        epoch=1956,
        max_zoom=18,
    ),
    LayerDefinition(
        id="interministerial-1973",
        name="Interministerial aerial (1973-1986)",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="Interministerial_1973-1986",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN historical orthophotography",
        description="Interministerial flight series covering the late-Franco and transition years.",
        default_opacity=0.9,
        epoch=1973,
        max_zoom=18,
    ),
    LayerDefinition(
        id="nacional-1981",
        name="National aerial (1981-1986)",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="Nacional_1981-1986",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN historical orthophotography",
        description="National flight series, the last coverage before large scale land consolidation.",
        default_opacity=0.9,
        epoch=1981,
        max_zoom=18,
    ),
    LayerDefinition(
        id="pnoa-2005",
        name="PNOA orthophoto 2005",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="PNOA2005",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN — Plan Nacional de Ortofotografía Aérea",
        description="Early PNOA colour orthophotography epoch.",
        default_opacity=0.9,
        epoch=2005,
        max_zoom=19,
    ),
    LayerDefinition(
        id="pnoa-2015",
        name="PNOA orthophoto 2015",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="PNOA2015",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN — Plan Nacional de Ortofotografía Aérea",
        description="Mid-decade PNOA epoch for medium term change detection.",
        default_opacity=0.9,
        epoch=2015,
        max_zoom=19,
    ),
    LayerDefinition(
        id="pnoa-2020",
        name="PNOA orthophoto 2020",
        group="historical",
        kind="wms",
        url=IGN_HISTORIC_ORTHO_WMS,
        wms_layers="PNOA2020",
        wms_format="image/png",
        wms_transparent=True,
        attribution="IGN — Plan Nacional de Ortofotografía Aérea",
        description="Recent PNOA epoch, directly comparable with the LiDAR surface.",
        default_opacity=0.9,
        epoch=2020,
        max_zoom=19,
    ),
]

_MAPBOX_LAYER = LayerDefinition(
    id="mapbox-satellite",
    name="Mapbox Satellite Streets",
    group="basemap",
    kind="tile",
    url="https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token={token}",
    attribution="© Mapbox © OpenStreetMap",
    description="Mapbox satellite imagery with street labels (requires MAPBOX_ACCESS_TOKEN).",
    max_zoom=22,
    requires_token=True,
)


def list_layers() -> list[LayerDefinition]:
    settings = get_settings()
    layers = list(_LAYERS)
    if settings.mapbox_access_token:
        layers.append(
            _MAPBOX_LAYER.model_copy(
                update={"url": _MAPBOX_LAYER.url.replace("{token}", settings.mapbox_access_token)}
            )
        )
    return layers


def historical_epochs() -> list[int]:
    return sorted({layer.epoch for layer in _LAYERS if layer.epoch is not None})
