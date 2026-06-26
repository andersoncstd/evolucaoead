import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import pyarrow.parquet as pq


st.set_page_config(
    page_title="Censo da Educação Superior",
    layout="wide"
)

st.title("Censo da Educação Superior — Visualização Interativa")

ARQUIVO_PARQUET = "censo_superior_agregado.parquet"

# =========================
# MAPEAMENTOS
# =========================

modality_map = {
    1: "Presencial",
    2: "A Distância"
}

categoria_map = {
    1: "Pública Federal",
    2: "Pública Estadual",
    3: "Pública Municipal",
    4: "Privada",
    5: "Especial",
    7: "Pública Distrital"
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

metricas_map = {
    "QT_MAT": "Matrículas",
    "QT_ING": "Ingressantes",
    "QT_INSCRITO_TOTAL": "Inscritos",
    "QT_CONC": "Concluintes",
    "QT_VAG_TOTAL": "Vagas"
}

agrupamento_map = {
    "Modalidade": "Modalidade",
    "Categoria Administrativa": "Categoria Administrativa",
    "Rede": "Rede",
    "Grau Acadêmico": "Grau Acadêmico",
    "NO_REGIAO": "Região",
    "SG_UF": "UF",
    "NO_UF": "Estado",
    "NO_MUNICIPIO": "Município",
    "NO_CINE_AREA_GERAL": "Área Geral",
    "NO_CINE_AREA_ESPECIFICA": "Área Específica",
    "NO_CURSO": "Curso"
}

color_map = {
    "Presencial": "#0072B2",
    "A Distância": "#E69F00",
    "Pública": "#0072B2",
    "Privada": "#E69F00",
    "Pública Federal": "#0072B2",
    "Pública Estadual": "#009E73",
    "Pública Municipal": "#CC79A7",
    "Pública Distrital": "#56B4E9",
    "Especial": "#D55E00",
    "Bacharelado": "#0072B2",
    "Licenciatura": "#009E73",
    "Tecnológico": "#E69F00",
    "Bacharelado e Licenciatura": "#CC79A7"
}

# =========================
# COLUNAS NECESSÁRIAS
# =========================

COLUNAS_BASE = [
    "Ano",
    "TP_MODALIDADE_ENSINO",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "TP_REDE",
    "TP_GRAU_ACADEMICO",
    "NO_REGIAO",
    "SG_UF",
    "NO_UF",
    "NO_MUNICIPIO",
    "NO_CINE_AREA_GERAL",
    "NO_CINE_AREA_ESPECIFICA",
    "NO_CURSO",
    "QT_MAT",
    "QT_ING",
    "QT_INSCRITO_TOTAL",
    "QT_CONC",
    "QT_VAG_TOTAL"
]

# =========================
# CARREGAMENTO
# =========================

@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados():
    caminho = Path(ARQUIVO_PARQUET)

    if not caminho.exists():
        st.error(
            "Arquivo censo_superior_agregado.parquet não encontrado. "
            "Verifique se ele está na raiz do repositório."
        )
        st.stop()

    colunas_disponiveis = pq.ParquetFile(caminho).schema.names
    colunas_para_ler = [col for col in COLUNAS_BASE if col in colunas_disponiveis]

    df = pd.read_parquet(
        caminho,
        columns=colunas_para_ler,
        engine="pyarrow"
    )

    if "Ano" not in df.columns and "NU_ANO_CENSO" in df.columns:
        df["Ano"] = df["NU_ANO_CENSO"]

    if "Ano" not in df.columns:
        st.error("A coluna 'Ano' ou 'NU_ANO_CENSO' não foi encontrada no arquivo.")
        st.stop()

    df["Ano"] = df["Ano"].astype(int)

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

# =========================
# CONFIGURAÇÕES DINÂMICAS
# =========================

colunas_metricas = [
    col for col in df.columns
    if col.startswith("QT_") and pd.api.types.is_numeric_dtype(df[col])
]

if not colunas_metricas:
    st.error("Nenhuma coluna métrica iniciada com 'QT_' foi encontrada.")
    st.stop()

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

if not colunas_agrupamento:
    st.error("Nenhuma coluna de agrupamento foi encontrada.")
    st.stop()

# =========================
# SIDEBAR
# =========================

st.sidebar.header("Filtros")

metrica_nome = st.sidebar.selectbox(
    "Métrica",
    options=colunas_metricas,
    format_func=lambda x: metricas_map.get(x, x),
    index=colunas_metricas.index("QT_MAT") if "QT_MAT" in colunas_metricas else 0
)

agrupamento = st.sidebar.selectbox(
    "Agrupar por",
    options=colunas_agrupamento,
    format_func=lambda x: agrupamento_map.get(x, x),
    index=colunas_agrupamento.index("Modalidade") if "Modalidade" in colunas_agrupamento else 0
)

anos = sorted(df["Ano"].dropna().unique())

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

# =========================
# FILTRAGEM
# =========================

df_filtrado = df[
    (df["Ano"] >= ano_min) &
    (df["Ano"] <= ano_max)
].copy()

df_filtrado = df_filtrado.dropna(subset=[agrupamento, metrica_nome])

top_categorias = (
    df_filtrado
    .groupby(agrupamento, observed=True)[metrica_nome]
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
    .groupby(["Ano", agrupamento], as_index=False, observed=True)[metrica_nome]
    .sum()
)

# =========================
# GRÁFICO
# =========================

nome_metrica = metricas_map.get(metrica_nome, metrica_nome)
nome_agrupamento = agrupamento_map.get(agrupamento, agrupamento)

titulo = f"Evolução de {nome_metrica} por {nome_agrupamento} ({ano_min}–{ano_max})"

if tipo_grafico == "Linha":
    fig = px.line(
        df_plot,
        x="Ano",
        y=metrica_nome,
        color=agrupamento,
        color_discrete_map=color_map,
        markers=True,
        title=titulo,
        labels={
            "Ano": "Ano",
            metrica_nome: nome_metrica,
            agrupamento: nome_agrupamento
        }
    )

    fig.update_traces(
        line=dict(width=4),
        marker=dict(size=9)
    )

elif tipo_grafico == "Barras":
    fig = px.bar(
        df_plot,
        x="Ano",
        y=metrica_nome,
        color=agrupamento,
        color_discrete_map=color_map,
        barmode="group",
        title=titulo,
        labels={
            "Ano": "Ano",
            metrica_nome: nome_metrica,
            agrupamento: nome_agrupamento
        }
    )

else:
    fig = px.area(
        df_plot,
        x="Ano",
        y=metrica_nome,
        color=agrupamento,
        color_discrete_map=color_map,
        title=titulo,
        labels={
            "Ano": "Ano",
            metrica_nome: nome_metrica,
            agrupamento: nome_agrupamento
        }
    )

fig.update_layout(
    hovermode="x unified",
    xaxis_title="Ano",
    yaxis_title=nome_metrica,
    legend_title=nome_agrupamento,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig.update_xaxes(
    dtick=1,
    showline=True,
    linecolor="black",
    linewidth=1,
    showgrid=True,
    gridcolor="lightgray"
)

fig.update_yaxes(
    showline=True,
    linecolor="black",
    linewidth=1,
    showgrid=True,
    gridcolor="lightgray"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# TABELA
# =========================

st.subheader("Dados agregados")

df_tabela = df_plot.rename(
    columns={
        metrica_nome: nome_metrica,
        agrupamento: nome_agrupamento
    }
)

st.dataframe(
    df_tabela.sort_values(["Ano", nome_metrica], ascending=[True, False]),
    use_container_width=True
)