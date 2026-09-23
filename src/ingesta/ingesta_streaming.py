"""
Ingesta STREAMING (simulada) -> Bronze.

Entra por esta via: validaciones de Transmetro y boardings de Aerometro.
Son eventos que en produccion llegan continuamente (un torniquete o un
boarding por vez).

Decision de tiempo (documentada en docs/decisiones.md): para la Fase 1 no
se levanto Kafka en Docker por la ventana de entrega. Se simula el
comportamiento del productor -> topico -> consumidor con un script que lee
el CSV linea por linea y las escribe a Bronze una por una, igual que lo
haria un consumer de Kafka escribiendo micro-batches. La interfaz (una
funcion "publicar_evento") esta separada de la escritura a Bronze
precisamente para poder sustituir esta simulacion por un productor/consumer
real de Kafka sin tocar el resto del pipeline.
"""
import csv
import os
import sys
from datetime import date

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import DATOS_RED, ruta_particion_bronze, ahora_utc_iso  # noqa: E402

FECHA_INGESTA = date.today().isoformat()

FUENTES_STREAMING = [
    ("tm_validaciones", "transmetro_validaciones.csv"),
    ("am_boardings", "aerometro_boardings.csv"),
]


def leer_eventos_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def publicar_evento(evento: dict, fuente: str) -> dict:
    """Simula la publicacion al topico: adjunta metadatos de evento."""
    evento = dict(evento)
    evento["ts_ingesta"] = ahora_utc_iso()
    evento["fuente_archivo"] = fuente
    return evento


def ingerir_streaming(con, fuente, archivo_csv):
    origen = os.path.join(DATOS_RED, archivo_csv)
    eventos = [publicar_evento(row, fuente) for row in leer_eventos_csv(origen)]
    if not eventos:
        return 0

    columnas = list(eventos[0].keys())
    destino = os.path.join(ruta_particion_bronze(fuente, FECHA_INGESTA), "part-000.parquet")

    con.execute(f"CREATE OR REPLACE TEMP TABLE _stg_{fuente} ({', '.join(f'{c} VARCHAR' for c in columnas)})")
    placeholders = ", ".join(["?"] * len(columnas))
    con.executemany(
        f"INSERT INTO _stg_{fuente} VALUES ({placeholders})",
        [[e[c] for c in columnas] for e in eventos],
    )
    con.execute(f"""
        COPY (
            SELECT *, DATE '{FECHA_INGESTA}' AS fecha_ingesta FROM _stg_{fuente}
        ) TO '{destino.replace(os.sep, "/")}' (FORMAT PARQUET)
    """)
    return len(eventos)


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
