"""Exporta las tablas de la capa Gold que lee el tablero a CSV (carpeta tableau/)."""
import os
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")
OUT_DIR = os.path.join(BASE_DIR, "tableau")

TABLAS = [
    "mart_demanda",
    "mart_cobertura_zona",
    "mart_transbordo",
    "mart_metroriel_zona",
    "mart_metroriel_od",
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    con = duckdb.connect(DB_PATH, read_only=True)
    for t in TABLAS:
        destino = os.path.join(OUT_DIR, f"{t}.csv").replace(os.sep, "/")
        con.execute(f"COPY main_gold.{t} TO '{destino}' (HEADER, DELIMITER ',')")
        n = con.execute(f"select count(*) from main_gold.{t}").fetchone()[0]
        print(f"  {t}.csv: {n} filas")
    con.close()


if __name__ == "__main__":
    main()
