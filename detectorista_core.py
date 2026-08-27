"""Lógica pura de análisis detectorista, independiente de Streamlit."""

from typing import Iterable, Tuple

import folium
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

LAT_RANGE = (-90.0, 90.0)
LON_RANGE = (-180.0, 180.0)

DEFAULT_LAT = 37.7701
DEFAULT_LON = -1.5020
DEFAULT_ZOOM = 16

FREE_REPORT = "Terreno público, no protegido → Interés detectorista: alto"
RESTRICTED_REPORT = "Terreno privado o protegido → No recomendable"


def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """Devuelve las coordenadas como flotantes, o lanza ValueError si no son válidas."""
    lat = float(lat)
    lon = float(lon)
    if not LAT_RANGE[0] <= lat <= LAT_RANGE[1]:
        raise ValueError(f"Latitud fuera de rango: {lat}")
    if not LON_RANGE[0] <= lon <= LON_RANGE[1]:
        raise ValueError(f"Longitud fuera de rango: {lon}")
    return lat, lon


def make_point(lat: float, lon: float) -> Point:
    """Crea un punto (lon, lat) validando las coordenadas."""
    lat, lon = validate_coordinates(lat, lon)
    return Point(lon, lat)


def is_free(point: Point, restricted_areas: Iterable[BaseGeometry] = ()) -> bool:
    """True si el punto no cae dentro de ninguna zona restringida."""
    return not any(area.intersects(point) for area in restricted_areas)


def marker_color(free: bool) -> str:
    return "green" if free else "red"


def marker_popup(free: bool) -> str:
    return "Libre" if free else "Prohibido"


def report_message(free: bool) -> str:
    return FREE_REPORT if free else RESTRICTED_REPORT


def build_map(lat: float, lon: float, free: bool, zoom: int = DEFAULT_ZOOM) -> folium.Map:
    """Construye el mapa con un marcador coloreado según el resultado del análisis."""
    lat, lon = validate_coordinates(lat, lon)
    mapa = folium.Map(location=[lat, lon], zoom_start=zoom)
    folium.Marker(
        [lat, lon],
        popup=marker_popup(free),
        icon=folium.Icon(color=marker_color(free)),
    ).add_to(mapa)
    return mapa


def analyze(
    lat: float,
    lon: float,
    restricted_areas: Iterable[BaseGeometry] = (),
    zoom: int = DEFAULT_ZOOM,
) -> Tuple[bool, str, folium.Map]:
    """Analiza unas coordenadas y devuelve (libre, informe, mapa)."""
    restricted_areas = tuple(restricted_areas)
    point = make_point(lat, lon)
    free = is_free(point, restricted_areas)
    return free, report_message(free), build_map(lat, lon, free, zoom)
