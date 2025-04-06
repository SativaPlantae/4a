import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
import os

st.set_page_config(page_title="Georreferenciamento", page_icon="🌍")
st.title("🌍 Verificador de Coordenadas Geográficas")
st.markdown("Insira uma coordenada em **UTM zona 22S - SIRGAS 2000 (EPSG:31982)** para verificar onde ela está e se há alguma restrição.")

col1, col2 = st.columns(2)
with col1:
    utm_x = st.number_input("Coordenada UTM (Leste - X)", value=0.0, format="%.3f")
with col2:
    utm_y = st.number_input("Coordenada UTM (Norte - Y)", value=0.0, format="%.3f")

def checar_intersecoes(ponto_gdf, pasta):
    resultados = {}
    for root, _, files in os.walk(pasta):
        for file in files:
            if file.endswith(".shp"):
                caminho = os.path.join(root, file)
                nome = os.path.splitext(file)[0]
                try:
                    gdf = gpd.read_file(caminho)
                    gdf = gdf.to_crs("EPSG:31982")
                    intersecta = gdf.intersects(ponto_gdf.geometry.iloc[0]).any()
                    resultados[nome] = "✅ Sim" if intersecta else "❌ Não"
                except Exception as e:
                    resultados[nome] = f"⚠️ Erro: {e}"
    return resultados

if st.button("🔍 Verificar Localização"):
    if utm_x == 0 or utm_y == 0:
        st.warning("Por favor, insira coordenadas válidas.")
    else:
        st.markdown(f"**📌 Coordenada UTM (SIRGAS 2000 / zona 22S):** {utm_x}, {utm_y}")
        ponto = gpd.GeoDataFrame(geometry=[Point(utm_x, utm_y)], crs="EPSG:31982")

        # Localização Administrativa com atributos
        st.subheader("📍 Localização Administrativa")
        atributos_admin = {
            "estados": "NM_UF",
            "municipios": "NM_MUN",
            "unidades_conservacao": "NomeUC"
        }

        for camada, coluna in atributos_admin.items():
            caminho_shp = os.path.join("camadas/administrativo", f"{camada}.shp")
            if os.path.exists(caminho_shp):
                try:
                    gdf = gpd.read_file(caminho_shp)
                    gdf = gdf.to_crs("EPSG:31982")
                    intersecao = gdf[gdf.intersects(ponto.geometry.iloc[0])]
                    if not intersecao.empty:
                        valor = intersecao.iloc[0][coluna]
                        st.success(f"**{camada}:** {valor}")
                    else:
                        st.error(f"**{camada}:** ❌ Não encontrado")
                except Exception as e:
                    st.warning(f"Erro ao processar {camada}: {e}")
            else:
                st.warning(f"Camada '{camada}' não encontrada.")

        # Licenciamento
        st.subheader("🛠️ Licenciamento")
        lic = checar_intersecoes(ponto, "camadas/licenciamento")
        for nome, status in lic.items():
            st.write(f"**{nome}:** {status}")

        # Restrições
        st.subheader("⛔ Restrições Ambientais")
        res = checar_intersecoes(ponto, "camadas/restricao")
        for nome, status in res.items():
            st.write(f"**{nome}:** {status}")

        # Conclusão
        st.subheader("📝 Conclusão")
        if any(v == "✅ Sim" for v in res.values()):
            st.error("A coordenada está em uma área com restrição ambiental. Intervenção não permitida.")
        elif any(v == "✅ Sim" for v in lic.values()):
            st.success("A coordenada está em área licenciada. Execução permitida, desde que não haja restrições.")
        else:
            st.warning("A coordenada não está licenciada nem possui restrição registrada.")
