import streamlit as st
from streamlit_folium import folium_static

from detectorista_core import DEFAULT_LAT, DEFAULT_LON, analyze


def main():
    st.title("Detectorista GIS - Totana")

    # Entradas de coordenadas
    lat = st.number_input("Latitud", value=DEFAULT_LAT, format="%.6f")
    lon = st.number_input("Longitud", value=DEFAULT_LON, format="%.6f")

    if st.button("Analizar"):
        # Análisis (añade shapefiles reales como zonas restringidas más adelante)
        libre, informe, mapa = analyze(lat, lon, restricted_areas=())

        folium_static(mapa)

        if libre:
            st.success(informe)
        else:
            st.error(informe)


if __name__ == "__main__":
    main()
