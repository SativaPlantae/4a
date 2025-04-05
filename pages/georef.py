import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer
import os

st.set_page_config(page_title="Georreferenciamento", page_icon="🌍")
st.title("🌍 Verificador de Coordenadas Geográficas")
st.markdown("Insira uma coordenada em **UTM zona 22S** para verificar onde ela está e se há alguma restrição.")

col1, col2 = st.columns(2)
with col1:
    utm_x = st.number_input("Coordenada UTM (Leste - X)", value=0.0, format="%.3f")
with col2:
    utm_y = st.number_input("Coordenada UTM (Norte - Y)", value=0.0, format="%.3f")

def utm22s_para_latlon(x, y):
    transformer = Transformer.from_crs("EPSG:32722", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon

def checar_intersecoes(ponto_gdf, pasta):
    resultados = {}
    for root, _, files in os.walk(pasta):
        for file in files:
            if file.endswith(".shp"):
                caminho = os.path.join(root, file)
                nome = os.path.splitext(file)[0]
                try:
                    gdf = gpd.read_file(caminho)
                    gdf = gdf.to_crs("EPSG:4326")
                    intersecta = gdf.intersects(ponto_gdf.geometry.iloc[0]).any()
                    resultados[nome] = "✅ Sim" if intersecta else "❌ Não"
                except Exception as e:
                    resultados[nome] = f"⚠️ Erro: {e}"
    return resultados

if st.button("🔍 Verificar Localização"):
    if utm_x == 0 or utm_y == 0:
        st.warning("Por favor, insira coordenadas válidas.")
    else:
        lat, lon = utm22s_para_latlon(utm_x, utm_y)
        st.markdown(f"**📌 Latitude/Longitude:** {lat:.6f}, {lon:.6f}")

        ponto = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")

        st.subheader("📍 Localização Administrativa")
        admin = checar_intersecoes(ponto, "camadas/Administrativa")
        for nome, status in admin.items():
            st.write(f"**{nome}:** {status}")

        st.subheader("🛠️ Licenciamento")
        lic = checar_intersecoes(ponto, "camadas/Licenciamentos")
        for nome, status in lic.items():
            st.write(f"**{nome}:** {status}")

        st.subheader("⛔ Restrições Ambientais")
        res = checar_intersecoes(ponto, "camadas/Restrições ambientais")
        for nome, status in res.items():
            st.write(f"**{nome}:** {status}")

        st.subheader("📝 Conclusão")
        if any(v == "✅ Sim" for v in res.values()):
            st.error("A coordenada está em uma área com restrição ambiental. Intervenção não permitida.")
        elif any(v == "✅ Sim" for v in lic.values()):
            st.success("A coordenada está em área licenciada. Execução permitida, desde que não haja restrições.")
        else:
            st.warning("A coordenada não está licenciada nem possui restrição registrada.")
