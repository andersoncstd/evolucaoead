import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Censo da Educação Superior",
    layout="wide"
)

st.title("Censo da Educação Superior — Visualização Interativa")

ARQUIVO_PARQUET = "censo_superior_agregado.parquet"

modality_map = {
    1: "Presencial",
    2: "A Distância"
}

categoria_map = {
    1: "Pública Federal",
    2: "Pública Estadual",
    3: "Pública Municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    7: "Especial"
}

rede_map = {
    1: "Pública",
    2: "Privada"
}

grau_map = {
    1: "Bacharelado",
    2: "Licenciatura",
    3: "Tecnológico",
    4: "Bacharelado e Licenciatura"
}

color_map = {
    'Privada': '#E69F00',          # Orange
    'Pública Federal': '#0072B2', # Blue
    'Pública Estadual': '#009E73',# Bluish Green
    'Outras Públicas': '#CC79A7', # Reddish Purple
    'Especial': '#D55E00'         # Vermillion
}


@st.cache_data
def carregar_dados():
    if not Path(ARQUIVO_PARQUET).exists():
        st.error(
            "Arquivo censo_superior_agregado.parquet não encontrado. "
            "Execute primeiro: uv run python preparar_dados.py"
        )
        st.stop()

    df = pd.read_parquet(ARQUIVO_PARQUET)

    if "TP_MODALIDADE_ENSINO" in df.columns:
        df["Modalidade"] = df["TP_MODALIDADE_ENSINO"].map(modality_map)

    if "TP_CATEGORIA_ADMINISTRATIVA" in df.columns:
        df["Categoria Administrativa"] = df["TP_CATEGORIA_ADMINISTRATIVA"].map(categoria_map)

    if "TP_REDE" in df.columns:
        df["Rede"] = df["TP_REDE"].map(rede_map)

    if "TP_GRAU_ACADEMICO" in df.columns:
        df["Grau Acadêmico"] = df["TP_GRAU_ACADEMICO"].map(grau_map)

    return df


df = carregar_dados()

colunas_metricas = [
    col for col in df.columns
    if col.startswith("QT_")
]



colunas_agrupamento = [
    "Modalidade",
    "Categoria Administrativa",
    "Rede",
    "Grau Acadêmico",
    "NO_REGIAO",
    "SG_UF",
    "NO_UF",
    "NO_MUNICIPIO",
    "NO_CINE_AREA_GERAL",
    "NO_CINE_AREA_ESPECIFICA",
    "NO_CURSO",
]

colunas_agrupamento = [
    col for col in colunas_agrupamento
    if col in df.columns
]

st.sidebar.header("Filtros")

metrica = st.sidebar.selectbox(
    "Métrica",
    colunas_metricas,
    index=colunas_metricas.index("QT_MAT") if "QT_MAT" in colunas_metricas else 0
)

agrupamento = st.sidebar.selectbox(
    "Agrupar por",
    colunas_agrupamento,
    index=colunas_agrupamento.index("Modalidade") if "Modalidade" in colunas_agrupamento else 0
)

anos = sorted(df["Ano"].unique())

ano_min, ano_max = st.sidebar.slider(
    "Intervalo de anos",
    min_value=int(min(anos)),
    max_value=int(max(anos)),
    value=(int(min(anos)), int(max(anos))),
    step=1
)

tipo_grafico = st.sidebar.selectbox(
    "Tipo de gráfico",
    ["Linha", "Barras", "Área"]
)

top_n = st.sidebar.slider(
    "Top N categorias",
    min_value=2,
    max_value=30,
    value=10
)

df_filtrado = df[
    (df["Ano"] >= ano_min) &
    (df["Ano"] <= ano_max)
].copy()

df_filtrado = df_filtrado.dropna(subset=[agrupamento])

top_categorias = (
    df_filtrado
    .groupby(agrupamento)[metrica]
    .sum()
    .sort_values(ascending=False)
    .head(top_n)
    .index
)

df_filtrado = df_filtrado[
    df_filtrado[agrupamento].isin(top_categorias)
]

df_plot = (
    df_filtrado
    .groupby(["Ano", agrupamento], as_index=False)[metrica]
    .sum()
)

titulo = f"Evolução de {metrica} por {agrupamento} ({ano_min}–{ano_max})"

if tipo_grafico == "Linha":
    fig = px.line(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        color_discrete_map=color_map,
        markers=True,
        title=titulo
    )

elif tipo_grafico == "Barras":
    fig = px.bar(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        color_discrete_map=color_map,
        barmode="group",
        title=titulo
    )

else:
    fig = px.area(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        color_discrete_map=color_map,
        title=titulo
    )

fig.update_layout(
    hovermode="x unified",
    xaxis_title="Ano",
    yaxis_title="Quantidade",
    legend_title=agrupamento
)

fig.update_xaxes(
    dtick=1,
    showline=True,
    linecolor="black",
    linewidth=1,
    showgrid=True
)

fig.update_yaxes(
    showline=True,
    linecolor="black",
    linewidth=1,
    showgrid=True
)

fig.update_xaxes(
    showline=True,
    linecolor='black',
    linewidth=1,   # aumenta a espessura
    mirror=False,
    showgrid=True
)
fig.update_yaxes(
    showline=True,
    linewidth=1,
    linecolor='black',
    showgrid=True,
)

fig.update_traces(
    line=dict(width=4),
    marker=dict(size=10)
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Dados agregados")

st.dataframe(
    df_plot.sort_values(["Ano", metrica], ascending=[True, False]),
    use_container_width=True
)
