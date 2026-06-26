import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Censo da Educação Superior",
    layout="wide"
)

st.title("Evolução dos Indicadores do Censo da Educação Superior")

# =========================
# Mapeamentos
# =========================

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

grau_map = {
    1: "Bacharelado",
    2: "Licenciatura",
    3: "Tecnológico",
    4: "Bacharelado e Licenciatura"
}

rede_map = {
    1: "Pública",
    2: "Privada"
}

# =========================
# Carregamento dos dados
# =========================

@st.cache_data
def carregar_dados():
    arquivos = {
        2018: "dados_2018.csv",
        #2019: "dados_2019.csv",
        #2020: "dados_2020.csv",
        #2021: "dados_2021.csv",
        #2022: "dados_2022.csv",
        #2023: "dados_2023.csv",
        2024: "dados_2024.csv"
    }

    dados = []

    for ano, caminho in arquivos.items():
        df = pd.read_csv(
            caminho,
            sep=";",
            encoding="latin1",
            low_memory=False
        )

        df["Ano"] = ano

        if "TP_MODALIDADE_ENSINO" in df.columns:
            df["Modalidade"] = df["TP_MODALIDADE_ENSINO"].map(modality_map)

        if "TP_CATEGORIA_ADMINISTRATIVA" in df.columns:
            df["Categoria Administrativa"] = df["TP_CATEGORIA_ADMINISTRATIVA"].map(categoria_map)

        if "TP_GRAU_ACADEMICO" in df.columns:
            df["Grau Acadêmico"] = df["TP_GRAU_ACADEMICO"].map(grau_map)

        if "TP_REDE" in df.columns:
            df["Rede"] = df["TP_REDE"].map(rede_map)

        dados.append(df)

    return pd.concat(dados, ignore_index=True)


df = carregar_dados()

# =========================
# Colunas disponíveis
# =========================

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
    "NO_CURSO"
]

colunas_agrupamento = [
    col for col in colunas_agrupamento
    if col in df.columns
]

# =========================
# Filtros laterais
# =========================

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

anos_disponiveis = sorted(df["Ano"].dropna().unique())

ano_min, ano_max = st.sidebar.slider(
    "Intervalo de anos",
    min_value=int(min(anos_disponiveis)),
    max_value=int(max(anos_disponiveis)),
    value=(int(min(anos_disponiveis)), int(max(anos_disponiveis))),
    step=1
)

tipo_grafico = st.sidebar.selectbox(
    "Tipo de gráfico",
    ["Linha", "Barras", "Área"]
)

top_n = st.sidebar.slider(
    "Mostrar Top N categorias",
    min_value=2,
    max_value=30,
    value=10
)

# =========================
# Aplicação dos filtros
# =========================

df_filtrado = df[
    (df["Ano"] >= ano_min) &
    (df["Ano"] <= ano_max)
].copy()

df_filtrado = df_filtrado.dropna(subset=[agrupamento])

# Pega as principais categorias no período
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

# =========================
# Gráfico
# =========================

titulo = f"Evolução de {metrica} por {agrupamento} ({ano_min}–{ano_max})"

if tipo_grafico == "Linha":
    fig = px.line(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        markers=True,
        title=titulo
    )

elif tipo_grafico == "Barras":
    fig = px.bar(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        barmode="group",
        title=titulo
    )

else:
    fig = px.area(
        df_plot,
        x="Ano",
        y=metrica,
        color=agrupamento,
        title=titulo
    )

fig.update_layout(
    hovermode="x unified",
    xaxis=dict(dtick=1),
    yaxis_title="Quantidade",
    xaxis_title="Ano",
    legend_title=agrupamento
)

fig.update_xaxes(
    showline=True,
    linecolor="black",
    linewidth=2,
    mirror=False,
    showgrid=True
)

fig.update_yaxes(
    showline=True,
    linecolor="black",
    linewidth=1,
    showgrid=True
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# Tabela de dados
# =========================

st.subheader("Dados agregados")

st.dataframe(
    df_plot.sort_values(["Ano", metrica], ascending=[True, False]),
    use_container_width=True
)
