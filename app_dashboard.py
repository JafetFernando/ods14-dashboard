import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

# Configuración de la página (Debe ir al inicio)
st.set_page_config(page_title="Vigilancia Marítima - ODS 14", layout="wide")

# Título y contexto
st.title("⚓ Dashboard de Vigilancia Marítima y Detección INDNR")
st.markdown("Sistema analítico interactivo alineado al **ODS 14: Vida Submarina**. Monitoreo de trayectorias cinemáticas para la detección de pesca Ilegal, No Declarada y No Reglamentada.")

# Carga de datos (Usamos caché para que no recargue el CSV pesando en cada clic)
@st.cache_data
def load_data():
    with zipfile.ZipFile("purse_seines.csv.zip", "r") as z:
        csv_filename = [name for name in z.namelist() if name.endswith('.csv') and not name.startswith('__MACOSX')][0]
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)
            
    df = df.dropna(subset=['speed', 'course'])
    
    # FORZAR FORMATO NUMÉRICO (Evita el error de datos en blanco)
    df['is_fishing'] = pd.to_numeric(df['is_fishing'], errors='coerce')
    df = df[df['is_fishing'].isin([0, 1])]
    
    # CREAR ETIQUETAS ELEGANTES PARA LAS GRÁFICAS
    df['Estado'] = df['is_fishing'].map({0: 'En Tránsito', 1: 'Pescando'})
    
    return df

df = load_data()

# PANEL LATERAL (Filtros)
st.sidebar.header("Filtros de Análisis")
estado_pesca = st.sidebar.selectbox("Estado de Actividad:", options=["Todos", "En Tránsito (0)", "Pescando (1)"])

# Aplicar filtros
if estado_pesca == "En Tránsito (0)":
    df_filtered = df[df['is_fishing'] == 0]
elif estado_pesca == "Pescando (1)":
    df_filtered = df[df['is_fishing'] == 1]
else:
    df_filtered = df

# SECCIÓN DE MÉTRICAS (KPIs)
col1, col2, col3 = st.columns(3)
col1.metric("Registros Analizados", f"{len(df_filtered):,}")
col2.metric("Embarcaciones Únicas (MMSI)", f"{df_filtered['mmsi'].nunique()}")
col3.metric("Velocidad Promedio (Nudos)", f"{df_filtered['speed'].mean():.2f}")

st.markdown("---")

# SECCIÓN VISUAL 1: MAPA ESPACIAL INTERACTIVO
st.subheader("🗺️ Mapeo Geoespacial de Trayectorias")
# Usamos Plotly Express para un mapa elegante
fig_map = px.scatter_mapbox(df_filtered, 
                            lat="lat", 
                            lon="lon", 
                            color="Estado", # <-- Cambiado aquí
                            hover_name="mmsi",
                            hover_data=["speed", "course", "distance_from_shore"],
                            color_discrete_map={"En Tránsito": "blue", "Pescando": "red"}, # <-- Colores directos
                            zoom=4, 
                            height=500)
fig_map.update_layout(mapbox_style="carto-positron")
st.plotly_chart(fig_map, use_container_width=True)

# SECCIÓN VISUAL 2: ANÁLISIS CINEMÁTICO
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Distribución de Velocidades")
    fig_hist = px.histogram(df_filtered, x="speed", color="Estado", nbins=50, 
                            title="Frecuencia de velocidades operativas",
                            color_discrete_map={"En Tránsito": "blue", "Pescando": "red"},
                            barmode="overlay")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_chart2:
    st.subheader("Relación Distancia a Costa vs Velocidad")
    fig_scatter = px.scatter(df_filtered, x="distance_from_shore", y="speed", color="Estado",
                             color_discrete_map={"En Tránsito": "blue", "Pescando": "red"},
                             title="Análisis de fronteras oceánicas")
    st.plotly_chart(fig_scatter, use_container_width=True)
