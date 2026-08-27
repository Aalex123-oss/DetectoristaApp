import streamlit as st
import folium
from streamlit_folium import folium_static
from shapely.geometry import Point

# Título de la app
st.title("Detectorista GIS - Totana")

# Entradas de coordenadas
lat = st.number_input("Latitud", value=37.7701, min_value=-90.0, max_value=90.0, format="%.6f")
lon = st.number_input("Longitud", value=-1.5020, min_value=-180.0, max_value=180.0, format="%.6f")

if st.button("Analizar"):
    # Crear punto
    punto = Point(lon, lat)
    
    # Simulación de análisis (reemplaza con shapefiles reales más adelante)
    libre = True  # True = libre, False = protegido/privado
    
    # Crear mapa
    m = folium.Map(location=[lat, lon], zoom_start=16)
    color = "green" if libre else "red"
    folium.Marker([lat, lon], popup="Libre" if libre else "Prohibido", icon=folium.Icon(color=color)).add_to(m)
    
    # Mostrar mapa
    folium_static(m)
    
    # Mostrar informe
    if libre:
        st.success("Terreno público, no protegido → Interés detectorista: alto")
    else:
        st.error("Terreno privado o protegido → No recomendable")
