"""Corre ingesta + dbt dos veces y compara el conteo de filas de cada tabla (1.5).

Uso: python src/ingesta/verificar_idempotencia.py
Deja la evidencia en docs/evidencia_idempotencia.json.
"""
import json
import os
import subprocess
import sys
import time

import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DBT_DIR = os.path.join(BASE_DIR, "dbt_project")
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")
DBT_EXE = os.path.join(os.path.dirname(sys.executable), "Scripts", "dbt.exe") if os.name == "nt" else "dbt"
ESQUEMAS = ("main_silver", "main_gold", "main_features")


def correr_pipeline():
    env = dict(os.environ)
    env["PROJECT_ROOT"] = BASE_DIR.replace("\\", "/")
    t0 = time.time()
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "src", "ingesta", "run_ingesta_bronze.py")],
                   check=True, capture_output=True)
    t1 = time.time()
    subprocess.run([DBT_EXE, "run", "--profiles-dir", DBT_DIR], cwd=DBT_DIR, env=env,
                   check=True, capture_output=True)
    t2 = time.time()
    return {"ingesta_s": round(t1 - t0, 1), "dbt_run_s": round(t2 - t1, 1)}


def contar():
    con = duckdb.connect(DB_PATH, read_only=True)
    tablas = con.execute(
        "select table_schema, table_name from information_schema.tables "
        f"where table_schema in {ESQUEMAS} order by 1, 2"
    ).fetchall()
    conteos = {f"{s}.{t}": con.execute(f"select count(*) from {s}.{t}").fetchone()[0] for s, t in tablas}
    con.close()
    return conteos


def main():
    tiempos1 = correr_pipeline()
    c1 = contar()
    tiempos2 = correr_pipeline()
    c2 = contar()

    print(f"{'tabla':50} {'corrida 1':>10} {'corrida 2':>10}")
    for t in c1:
        marca = "" if c1[t] == c2[t] else "   <-- DIFERENTE"
        print(f"{t:50} {c1[t]:>10} {c2[t]:>10}{marca}")
    idempotente = c1 == c2
    print(f"\nTiempos corrida 1: {tiempos1}  corrida 2: {tiempos2}")
    print("Resultado:", "IDEMPOTENTE, conteos identicos" if idempotente else "NO es idempotente")

    with open(os.path.join(BASE_DIR, "docs", "evidencia_idempotencia.json"), "w", encoding="utf-8") as f:
        json.dump({"corrida_1": c1, "corrida_2": c2, "tiempos_corrida_1": tiempos1,
                   "tiempos_corrida_2": tiempos2, "idempotente": idempotente}, f, indent=2, ensure_ascii=False)
    return 0 if idempotente else 1


if __name__ == "__main__":
    sys.exit(main())
