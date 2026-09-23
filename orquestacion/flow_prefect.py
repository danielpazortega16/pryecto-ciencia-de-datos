"""
Orquestacion del flujo completo con Prefect (1.5).

Corre: ingesta a Bronze (streaming simulado + batch + CDC) -> dbt run
(staging -> silver -> gold) -> dbt test. Idempotente: se puede correr
tantas veces como se quiera el mismo dia sin duplicar nada (Bronze
sobreescribe la particion del dia, Silver/Gold son tablas recalculadas
por completo en cada corrida).

Uso:
    python orquestacion/flow_prefect.py
"""
import os
import subprocess
import sys

from prefect import flow, task

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DBT_PROJECT_DIR = os.path.join(BASE_DIR, "dbt_project")
DBT_EXE = os.path.join(
    os.path.dirname(sys.executable), "Scripts", "dbt.exe"
) if os.name == "nt" else "dbt"


@task(retries=1, retry_delay_seconds=10)
def ingesta_bronze():
    sys.path.insert(0, os.path.join(BASE_DIR, "src", "ingesta"))
    import run_ingesta_bronze
    return run_ingesta_bronze.main()


@task(retries=1, retry_delay_seconds=10)
def dbt_run():
    env = dict(os.environ)
    env["PROJECT_ROOT"] = BASE_DIR.replace("\\", "/")
    resultado = subprocess.run(
        [DBT_EXE, "run", "--profiles-dir", DBT_PROJECT_DIR],
        cwd=DBT_PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    print(resultado.stdout)
    if resultado.returncode != 0:
        print(resultado.stderr, file=sys.stderr)
        raise RuntimeError("dbt run fallo, ver bitacora arriba")
    return resultado.stdout


@task
def dbt_test():
    env = dict(os.environ)
    env["PROJECT_ROOT"] = BASE_DIR.replace("\\", "/")
    resultado = subprocess.run(
        [DBT_EXE, "test", "--profiles-dir", DBT_PROJECT_DIR],
        cwd=DBT_PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    print(resultado.stdout)
    # dbt test no es bloqueante para el flujo: se reporta pero no se corta,
    # las pruebas de calidad de dato ya se resuelven via cuarentena.
    return resultado.returncode == 0


@flow(name="red-metropolitana-pipeline")
def pipeline_completo():
    conteos_bronze = ingesta_bronze()
    dbt_run()
    tests_ok = dbt_test()
    print(f"Conteos Bronze: {conteos_bronze}")
    print(f"dbt test paso: {tests_ok}")
    return conteos_bronze


if __name__ == "__main__":
    pipeline_completo()
