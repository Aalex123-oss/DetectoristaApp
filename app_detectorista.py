import logging

import folium
import streamlit as st
from shapely.geometry import Point
from streamlit_folium import folium_static

logger = logging.getLogger(__name__)

MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0


def validar_coordenadas(lat, lon):
    """Devuelve la lista de errores de validación de las coordenadas."""
    errores = []
    if not MIN_LAT <= lat <= MAX_LAT:
        errores.append(f"La latitud debe estar entre {MIN_LAT} y {MAX_LAT} (recibido: {lat}).")
    if not MIN_LON <= lon <= MAX_LON:
        errores.append(f"La longitud debe estar entre {MIN_LON} y {MAX_LON} (recibido: {lon}).")
    return errores


def analizar_punto(punto):
    """Analiza el punto y devuelve True si el terreno es libre.

    Simulación de análisis (reemplaza con shapefiles reales más adelante).
    """
    if punto.is_empty:
        raise ValueError("El punto generado no es válido.")
    return True


def construir_mapa(lat, lon, libre):
    m = folium.Map(location=[lat, lon], zoom_start=16)
    color = "green" if libre else "red"
    folium.Marker(
        [lat, lon],
        popup="Libre" if libre else "Prohibido",
        icon=folium.Icon(color=color),
    ).add_to(m)
    return m


# Título de la app
st.title("Detectorista GIS - Totana")

# Entradas de coordenadas
lat = st.number_input("Latitud", value=37.7701, format="%.6f")
lon = st.number_input("Longitud", value=-1.5020, format="%.6f")

if st.button("Analizar"):
    errores = validar_coordenadas(lat, lon)
    if errores:
        for error in errores:
            st.error(error)
        st.stop()

    try:
        punto = Point(lon, lat)
        libre = analizar_punto(punto)
    except Exception:
        logger.exception("Error al analizar el punto (lat=%s, lon=%s)", lat, lon)
        st.error("No se pudo analizar la ubicación. Revisa las coordenadas e inténtalo de nuevo.")
        st.stop()

    try:
        folium_static(construir_mapa(lat, lon, libre))
    except Exception:
        logger.exception("Error al generar el mapa (lat=%s, lon=%s)", lat, lon)
        st.warning("No se pudo mostrar el mapa, pero el análisis del terreno sí se completó.")

    # Mostrar informe
    if libre:
        st.success("Terreno público, no protegido → Interés detectorista: alto")
    else:
        st.error("Terreno privado o protegido → No recomendable")
