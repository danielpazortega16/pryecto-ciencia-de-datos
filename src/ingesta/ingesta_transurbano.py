"""
Ingesta de Transurbano -> Bronze. Via elegida: BATCH.

Justificacion (Transurbano quedaba a criterio del equipo, ver docs/decisiones.md):
el archivo trae fecha y hora en columnas separadas y el monto ya en centavos,
la forma tipica de un extracto de liquidacion que un operador entrega
consolidado al cierre de un periodo, no un evento que haya que capturar en
el instante en que ocurre. Meterlo por streaming solo agregaria la
complejidad de un topico sin ganar nada: nadie en la Agencia necesita saber
en tiempo real que alguien abordo un bus de Transurbano, y el propio archivo
ya llega como lote. Consecuencia de esta decision: Transurbano siempre vivira
con mas latencia que Transmetro/Aerometro (el lote de hoy se ve hasta que
se procese), aceptable porque ningun requerimiento de la Fase 2 pide
demanda de Transurbano en tiempo real.
"""
import os
import sys
from datetime import date

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import DATOS_RED, ruta_particion_bronze, ahora_utc_iso  # noqa: E402

FECHA_INGESTA = date.today().isoformat()
TS_INGESTA = ahora_utc_iso()


def main():
    fuente = "tu_transacciones"
    origen = os.path.join(DATOS_RED, "transurbano_transacciones.csv")
    destino = os.path.join(ruta_particion_bronze(fuente, FECHA_INGESTA), "part-000.parquet")

    con = duckdb.connect()
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
    print(f"Ingesta BATCH (Transurbano) -> Bronze completada: {n} filas")
    con.close()
    return n


if __name__ == "__main__":
    main()
