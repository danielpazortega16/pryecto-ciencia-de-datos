"""
Orquestacion del flujo completo con Prefect.

Corre: ingesta a Bronze (streaming simulado + batch + CDC) -> dbt run
(staging -> silver -> gold) -> dbt test -> exportacion a CSV para Tableau
-> features de los cortes A, B y C (Proyecto 2).

Con --desde-cero primero vacia el lake (bronze/), el warehouse y los
artefactos de dbt, que es como hay que cargar datos nuevos que reemplazan a
los anteriores. Deja la tabla de conteos contra lo esperado y el tiempo de
cada etapa en docs/proyecto2/.

Uso:
    python orquestacion/flow_prefect.py --desde-cero
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
import time

from prefect import flow, task

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DBT_PROJECT_DIR = os.path.join(BASE_DIR, "dbt_project")
DBT_EXE = os.path.join(
    os.path.dirname(sys.executable), "Scripts", "dbt.exe"
) if os.name == "nt" else "dbt"
DOCS_P2 = os.path.join(BASE_DIR, "docs", "proyecto2")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src", "ingesta"))


def _env_dbt():
    env = dict(os.environ)
    env["PROJECT_ROOT"] = BASE_DIR.replace("\\", "/")
    return env


@task
def vaciar():
    for ruta in ("bronze", os.path.join("dbt_project", "target"), "warehouse.duckdb", "warehouse.duckdb.wal"):
        completa = os.path.join(BASE_DIR, ruta)
        if os.path.isdir(completa):
            shutil.rmtree(completa)
        elif os.path.exists(completa):
            os.remove(completa)


@task(retries=1, retry_delay_seconds=10)
def ingesta_bronze():
    import run_ingesta_bronze
    return run_ingesta_bronze.main()


@task(retries=1, retry_delay_seconds=10)
def dbt_run():
    resultado = subprocess.run(
        [DBT_EXE, "run", "--profiles-dir", DBT_PROJECT_DIR],
        cwd=DBT_PROJECT_DIR, env=_env_dbt(), capture_output=True, text=True,
    )
    print(resultado.stdout)
    if resultado.returncode != 0:
        print(resultado.stderr, file=sys.stderr)
        raise RuntimeError("dbt run fallo, ver bitacora arriba")
    return resultado.stdout


@task
def dbt_test():
    resultado = subprocess.run(
        [DBT_EXE, "test", "--profiles-dir", DBT_PROJECT_DIR],
        cwd=DBT_PROJECT_DIR, env=_env_dbt(), capture_output=True, text=True,
    )
    print(resultado.stdout)
    # dbt test no corta el flujo: se reporta. Las reglas de calidad del dato
    # ya se resuelven via cuarentena.
    return resultado.returncode == 0


@task
def exportar_tableau():
    import exportar_tableau as exp
    exp.main()


@task
def features_cortes():
    from ml.construir_dataset import main as construir
    return construir()


def _escribir_reportes(conteos, tiempos):
    os.makedirs(DOCS_P2, exist_ok=True)
    esperados = os.path.join(BASE_DIR, "orquestacion", "conteos_esperados.csv")
    with open(esperados, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    with open(os.path.join(DOCS_P2, "conteos_carga.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "filas_esperadas", "filas_cargadas", "diferencia"])
        for fila in filas:
            cargadas = conteos.get(fila["fuente_bronze"])
            esperadas = int(fila["filas_esperadas"])
            w.writerow([fila["archivo"], esperadas, cargadas,
                        "" if cargadas is None else cargadas - esperadas])
    with open(os.path.join(DOCS_P2, "tiempos_carga.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["etapa", "segundos"])
        for etapa, seg in tiempos.items():
            w.writerow([etapa, f"{seg:.1f}"])


@flow(name="red-metropolitana-pipeline")
def pipeline_completo(desde_cero: bool = False, con_features: bool = True):
    tiempos = {}

    def medir(nombre, fn):
        t0 = time.perf_counter()
        resultado = fn()
        tiempos[nombre] = time.perf_counter() - t0
        return resultado

    if desde_cero:
        medir("vaciar lake y warehouse", vaciar)
    conteos = medir("ingesta a bronze", ingesta_bronze)
    medir("dbt run (staging, silver, gold)", dbt_run)
    tests_ok = medir("dbt test", dbt_test)
    medir("exportar csv del tablero", exportar_tableau)
    if con_features:
        medir("features cortes A, B y C", features_cortes)
    tiempos["total"] = sum(tiempos.values())

    if desde_cero:
        _escribir_reportes(conteos, tiempos)
    print(f"Conteos Bronze: {conteos}")
    print(f"dbt test paso: {tests_ok}")
    for etapa, seg in tiempos.items():
        print(f"  {etapa:35s} {seg:7.1f} s")
    return conteos


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde-cero", action="store_true",
                        help="vacia bronze, warehouse y target de dbt antes de cargar")
    parser.add_argument("--sin-features", action="store_true")
    args = parser.parse_args()
    pipeline_completo(desde_cero=args.desde_cero, con_features=not args.sin_features)
