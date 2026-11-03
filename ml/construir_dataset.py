"""Construye la tabla de features de los cortes A, B y C (1.3) y la guarda.

Deja la tabla en el warehouse (main_ml.features) y en
ml/salidas/features_cortes.parquet, y escribe la tabla de poblacion (1.2).

Uso:
    python -m ml.construir_dataset
"""
import os

import duckdb

from ml.config import CORTES, DB_PATH, DOCS_P2, SALIDAS
from ml.features import tabla_cortes


def main():
    df = tabla_cortes(CORTES)
    df.to_parquet(os.path.join(SALIDAS, "features_cortes.parquet"), index=False)

    con = duckdb.connect(DB_PATH)
    con.execute("create schema if not exists main_ml")
    con.register("df_features", df)
    con.execute("create or replace table main_ml.features as select * from df_features")
    con.close()

    filas = []
    for corte, grupo in df.groupby("corte", sort=True):
        pob = len(grupo)
        if grupo["etiqueta"].notna().any():
            pos = int(grupo["etiqueta"].sum())
            filas.append(f"| {corte} | {grupo['fecha_corte'].iloc[0]} | {pob:,} | {pos:,} | {pos / pob:.4f} | {pos:,} / {pob:,} = {pos / pob:.4f} |")
        else:
            filas.append(f"| {corte} | {grupo['fecha_corte'].iloc[0]} | {pob:,} | etiqueta oculta | - | - |")
    with open(os.path.join(DOCS_P2, "poblacion.md"), "w", encoding="utf-8") as f:
        f.write("| Corte | Fecha | Poblacion | Positivos | Tasa positiva | Cuenta |\n|---|---|---:|---:|---:|---|\n")
        f.write("\n".join(filas) + "\n")
    print("\n".join(filas))
    return {c: len(g) for c, g in df.groupby("corte")}


if __name__ == "__main__":
    main()
