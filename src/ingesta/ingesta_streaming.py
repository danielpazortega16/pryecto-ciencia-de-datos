"""
Ingesta STREAMING (simulada) -> Bronze.

Entra por esta via: validaciones de Transmetro y boardings de Aerometro.
Son eventos que en produccion llegan continuamente (un torniquete o un
boarding por vez).

Decision de tiempo (documentada en docs/decisiones.md): para la Fase 1 no
se levanto Kafka en Docker por la ventana de entrega. Se simula el
comportamiento de un consumer que recibe el topico y lo escribe a Bronze
en microbatches (asi es como se implementa esto en produccion tambien: un
consumer real jamas hace un INSERT por evento, acumula y flushea). Cada
fila queda marcada con el momento de la ingesta y su fuente. Si mas
adelante se conecta un Kafka real, solo cambia de donde viene el CSV, esta
funcion de escritura a Bronze no se toca.
"""
import os
import sys
from datetime import date

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import DATOS_RED, ruta_particion_bronze, ahora_utc_iso  # noqa: E402

FECHA_INGESTA = date.today().isoformat()
TS_INGESTA = ahora_utc_iso()

FUENTES_STREAMING = [
    ("tm_validaciones", "transmetro_validaciones.csv"),
    ("am_boardings", "aerometro_boardings.csv"),
]


def ingerir_streaming(con, fuente, archivo_csv):
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


def main():
    con = duckdb.connect()
    conteos = {}
    for fuente, archivo in FUENTES_STREAMING:
        conteos[fuente] = ingerir_streaming(con, fuente, archivo)

    print("Ingesta STREAMING (simulada) -> Bronze completada")
    for fuente, n in conteos.items():
        print(f"  - {fuente}: {n} eventos publicados")
    con.close()
    return conteos


if __name__ == "__main__":
    main()
