"""
Ingesta CDC -> Bronze.

Entra por esta via: el padron de usuarios de Transmetro. Es el unico archivo
que se actualiza y se borra (los demas solo crecen), asi que se trata como
un log de cambios (INSERT/UPDATE/DELETE) y no como una carga completa.

Bronze guarda el log de cambios tal como llego, sin aplicar todavia ninguna
operacion (eso ocurre en Staging, ver dbt_project/models/staging/stg_padron_transmetro.sql).
Los DELETE llegan con la llave y sin cuerpo (nombre/estado vacios): eso se
conserva igual en Bronze, no se rellena nada aqui.
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
    fuente = "cdc_padron_usuarios"
    origen = os.path.join(DATOS_RED, "cdc_padron_usuarios.csv")
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
    print(f"Ingesta CDC (padron Transmetro) -> Bronze completada: {n} eventos")
    con.close()
    return n


if __name__ == "__main__":
    main()
