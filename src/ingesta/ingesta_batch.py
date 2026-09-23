"""
Ingesta BATCH -> Bronze.

Entra por esta via: los 4 catalogos de estaciones/paradas (cambian rara vez)
y los viajes de MetroRiel (llegan como viaje ya cerrado, no evento por evento).

Bronze conserva el dato tal como llego, mas fecha_ingesta (particion) y
ts_ingesta (marca de tiempo exacta). Vive en un lake de carpetas + Parquet,
no en el warehouse: uno de los archivos (MetroRiel) es JSON anidado y
forzarlo a una tabla relacional en el aterrizaje solo para descartar
estructura despues es trabajo de mas; el warehouse arranca en Staging/Silver.
"""
import os
import sys
from datetime import date

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import DATOS_RED, ruta_particion_bronze, ahora_utc_iso  # noqa: E402

FECHA_INGESTA = date.today().isoformat()
TS_INGESTA = ahora_utc_iso()

CATALOGOS_CSV = [
    ("tm_estaciones", "tm_estaciones.csv"),
    ("tu_paradas", "tu_paradas.csv"),
    ("mr_estaciones", "mr_estaciones.csv"),
    ("am_estaciones", "am_estaciones.csv"),
]


def ingerir_catalogo(con, fuente, archivo_csv):
    origen = os.path.join(DATOS_RED, archivo_csv)
    destino = os.path.join(ruta_particion_bronze(fuente, FECHA_INGESTA), "part-000.parquet")
    con.execute(f"""
        COPY (
            SELECT
                *,
                '{TS_INGESTA}'::TIMESTAMP AS ts_ingesta,
                DATE '{FECHA_INGESTA}' AS fecha_ingesta,
                '{fuente}' AS fuente_archivo
            FROM read_csv_auto('{origen.replace(os.sep, "/")}', header=true, all_varchar=true)
        ) TO '{destino.replace(os.sep, "/")}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{destino.replace(os.sep, '/')}')").fetchone()[0]
    return n


def ingerir_metroriel_viajes(con):
    fuente = "mr_viajes"
    origen = os.path.join(DATOS_RED, "metroriel_viajes.jsonl")
    destino = os.path.join(ruta_particion_bronze(fuente, FECHA_INGESTA), "part-000.parquet")
    con.execute(f"""
        COPY (
            SELECT
                *,
                '{TS_INGESTA}'::TIMESTAMP AS ts_ingesta,
                DATE '{FECHA_INGESTA}' AS fecha_ingesta,
                '{fuente}' AS fuente_archivo
            FROM read_json_auto('{origen.replace(os.sep, "/")}', format='newline_delimited')
        ) TO '{destino.replace(os.sep, "/")}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{destino.replace(os.sep, '/')}')").fetchone()[0]
    return n


def main():
    con = duckdb.connect()
    conteos = {}
    for fuente, archivo in CATALOGOS_CSV:
        conteos[fuente] = ingerir_catalogo(con, fuente, archivo)
    conteos["mr_viajes"] = ingerir_metroriel_viajes(con)

    print("Ingesta BATCH -> Bronze completada")
    for fuente, n in conteos.items():
        print(f"  - {fuente}: {n} filas")
    con.close()
    return conteos


if __name__ == "__main__":
    main()
