"""Auditoria de fuga (1.3): prueba de recorte de las features del corte A.

Calcula las features del corte A dos veces, con los datos completos y con
los datos recortados al 30 de junio, y compara las tablas.

  --nivel silver  recorta los eventos de Silver y el CDC antes de calcular.
  --nivel crudo   recorta los archivos crudos de datos_red, corre el pipeline
                  completo (ingesta, dbt) en una copia aislada del proyecto y
                  calcula ahi las features. Es la version estricta: atrapa
                  tambien fugas que vengan del pipeline y no solo de las
                  features.

Uso:
    python -m ml.prueba_recorte --nivel silver
    python -m ml.prueba_recorte --nivel crudo
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

import pandas as pd

from ml.config import BASE_DIR, CORTES, DOCS_P2
from ml.features import COLUMNAS_FEATURES, conectar, construir, preparar_vistas

CORTE = CORTES["A"]
LIMITE = datetime.combine(CORTE, datetime.min.time())


def features_completas():
    con = conectar()
    try:
        preparar_vistas(con)
        return construir(con, CORTE, con_etiqueta=False)
    finally:
        con.close()


def features_recorte_silver():
    con = conectar()
    try:
        preparar_vistas(con, datos_hasta=LIMITE)
        return construir(con, CORTE, con_etiqueta=False)
    finally:
        con.close()


def recortar_crudos(origen, destino, limite=LIMITE):
    os.makedirs(destino, exist_ok=True)
    for nombre in os.listdir(origen):
        src = os.path.join(origen, nombre)
        dst = os.path.join(destino, nombre)
        if nombre in ("tm_estaciones.csv", "tu_paradas.csv", "mr_estaciones.csv", "am_estaciones.csv"):
            shutil.copy(src, dst)
            continue
        if nombre == "metroriel_viajes.jsonl":
            with open(src, encoding="utf-8") as fi, open(dst, "w", encoding="utf-8") as fo:
                for linea in fi:
                    reg = json.loads(linea)
                    entrada = datetime.fromisoformat(reg["entry"]["ts"])
                    salida = reg["exit"]["ts"] if reg["exit"] else None
                    # A las 00:00 del corte un viaje solo existe en el archivo si ya
                    # se cerro (o quedo sin salida antes del corte).
                    if entrada < limite and (salida is None or datetime.fromisoformat(salida) < limite):
                        fo.write(linea)
            continue
        with open(src, newline="", encoding="utf-8") as fi, open(dst, "w", newline="", encoding="utf-8") as fo:
            r = csv.reader(fi)
            w = csv.writer(fo)
            cab = next(r)
            w.writerow(cab)
            idx = {c: i for i, c in enumerate(cab)}
            for fila in r:
                if nombre == "transmetro_validaciones.csv":
                    ts = datetime.strptime(fila[idx["fecha_hora"]], "%Y-%m-%d %H:%M:%S")
                elif nombre == "transurbano_transacciones.csv":
                    ts = datetime.strptime(fila[idx["fecha"]] + " " + fila[idx["hora"]], "%d/%m/%Y %H:%M:%S")
                elif nombre == "aerometro_boardings.csv":
                    ts = datetime.strptime(fila[idx["timestamp_utc"]], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=6)
                elif nombre == "cdc_padron_usuarios.csv":
                    ts = datetime.fromisoformat(fila[idx["commit_ts"]])
                else:
                    raise ValueError(f"Archivo no esperado: {nombre}")
                if ts < limite:
                    w.writerow(fila)


def features_recorte_crudo():
    tmp = tempfile.mkdtemp(prefix="recorte_")
    copia = os.path.join(tmp, "proyecto")
    archivos = subprocess.run(["git", "ls-files"], cwd=BASE_DIR, capture_output=True, text=True, check=True).stdout.split("\n")
    for rel in filter(None, archivos):
        if rel.startswith(("tableau/", "docs/")):
            continue
        destino = os.path.join(copia, rel)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy(os.path.join(BASE_DIR, rel), destino)
    recortar_crudos(os.path.join(BASE_DIR, "datos_red"), os.path.join(copia, "datos_red"))
    os.makedirs(os.path.join(copia, "tableau"), exist_ok=True)
    os.makedirs(os.path.join(copia, "docs", "proyecto2"), exist_ok=True)

    subprocess.run([sys.executable, "orquestacion/flow_prefect.py", "--desde-cero", "--sin-features"],
                   cwd=copia, check=True, capture_output=True, text=True)
    salida = os.path.join(tmp, "features_a.parquet")
    codigo = (
        "from ml.features import conectar, preparar_vistas, construir; from ml.config import CORTES;"
        "con = conectar(); preparar_vistas(con);"
        f"construir(con, CORTES['A'], con_etiqueta=False).to_parquet(r'{salida}', index=False)"
    )
    subprocess.run([sys.executable, "-c", codigo], cwd=copia, check=True, capture_output=True, text=True)
    df = pd.read_parquet(salida)
    df["fecha_corte"] = pd.to_datetime(df["fecha_corte"]).dt.date
    shutil.rmtree(tmp, ignore_errors=True)
    return df


def comparar(completo, recorte):
    cols = ["unidad_id", "fecha_corte", "tarjetas"] + COLUMNAS_FEATURES
    a = completo[cols].sort_values("unidad_id").reset_index(drop=True)
    b = recorte[cols].sort_values("unidad_id").reset_index(drop=True)
    resultado = {"filas_completo": len(a), "filas_recorte": len(b)}
    if len(a) != len(b) or not (a["unidad_id"].values == b["unidad_id"].values).all():
        solo_a = set(a["unidad_id"]) - set(b["unidad_id"])
        solo_b = set(b["unidad_id"]) - set(a["unidad_id"])
        resultado.update(diferencias=len(solo_a) + len(solo_b), features_con_diferencias=["poblacion"],
                         unidades_solo_completo=len(solo_a), unidades_solo_recorte=len(solo_b))
        return resultado
    malas = []
    total = 0
    for c in cols[1:]:
        if pd.api.types.is_float_dtype(a[c]):
            dif = ~((a[c] - b[c]).abs() < 1e-9) & ~(a[c].isna() & b[c].isna())
        else:
            dif = (a[c].astype(str) != b[c].astype(str))
        n = int(dif.sum())
        if n:
            malas.append(f"{c} ({n})")
            total += n
    resultado.update(diferencias=total, features_con_diferencias=malas)
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nivel", choices=["silver", "crudo"], default="silver")
    args = parser.parse_args()
    completo = features_completas()
    recorte = features_recorte_silver() if args.nivel == "silver" else features_recorte_crudo()
    res = comparar(completo, recorte)
    res["nivel"] = args.nivel
    res["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    with open(os.path.join(DOCS_P2, f"prueba_recorte_{args.nivel}.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    return res


if __name__ == "__main__":
    main()
