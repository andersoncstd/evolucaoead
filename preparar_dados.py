import pandas as pd
from pathlib import Path

ARQUIVOS = {
    2018: "dados_2018.csv",
    2019: "dados_2019.csv",
    2020: "dados_2020.csv",
    2021: "dados_2021.csv",
    2022: "dados_2022.csv",
    2023: "dados_2023.csv",
    2024: "dados_2024.csv",
}

COLUNAS_DIMENSAO = [
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
]

COLUNAS_METRICAS = [
    "QT_MAT",
    "QT_ING",
    "QT_CONC",
    "QT_INSCRITO_TOTAL",
    "QT_VG_TOTAL",
    "QT_CURSO",
    "QT_SIT_TRANCADA",
    "QT_SIT_DESVINCULADO",
    "QT_SIT_TRANSFERIDO",
]

COLUNAS_USADAS = COLUNAS_DIMENSAO + COLUNAS_METRICAS


def ler_csv(ano, caminho):
    print(f"Lendo {caminho}...")

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        usecols=lambda col: col in COLUNAS_USADAS,
        low_memory=False,
    )

    df["Ano"] = ano

    for col in COLUNAS_METRICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def main():
    dados_agregados = []

    for ano, caminho in ARQUIVOS.items():
        if not Path(caminho).exists():
            print(f"Arquivo não encontrado: {caminho}")
            continue

        df = ler_csv(ano, caminho)

        colunas_agrupamento = ["Ano"] + [
            col for col in COLUNAS_DIMENSAO if col in df.columns
        ]

        metricas_existentes = [
            col for col in COLUNAS_METRICAS if col in df.columns
        ]

        df_agg = (
            df.groupby(colunas_agrupamento, dropna=False, as_index=False)[metricas_existentes]
            .sum()
        )

        dados_agregados.append(df_agg)

        del df

    df_final = pd.concat(dados_agregados, ignore_index=True)

    df_final.to_parquet(
        "censo_superior_agregado.parquet",
        index=False
    )

    print("Arquivo gerado: censo_superior_agregado.parquet")
    print(f"Linhas finais: {len(df_final):,}")


if __name__ == "__main__":
    main()
