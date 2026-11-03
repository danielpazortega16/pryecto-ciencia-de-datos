"""Ensayo de la prueba de invariancia (2.4) con el corte B.

El dia de la defensa se corren el flujo y predecir.py con 30 dias mas de
datos y el corte del 30 de agosto, y las predicciones deben salir
identicas. No tenemos septiembre, pero con el corte B (31 de julio) se puede
hacer exactamente lo mismo:

  1. predecir.py con los archivos crudos recortados al 31 de julio
     (lo que habria existido ese dia).
  2. predecir.py con los datos completos, que traen 30 dias mas.
  3. Comparar los dos CSV byte por byte.

Al final vuelve a cargar datos_red completo y deja las predicciones del
corte C regeneradas, para no dejar el warehouse con datos recortados.

Uso:
    python -m ml.prueba_invariancia
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

import pandas as pd

from ml.config import BASE_DIR, CORTES, DOCS_P2
from ml.prueba_recorte import recortar_crudos


def predecir(carpeta, corte, salida):
    subprocess.run([sys.executable, "-W", "ignore", "predecir.py", "--datos", carpeta,
                    "--fecha-corte", corte.isoformat(), "--salida", salida],
                   cwd=BASE_DIR, check=True, capture_output=True, text=True)


def main():
    corte = CORTES["B"]
    tmp = tempfile.mkdtemp(prefix="invariancia_")
    recortados = os.path.join(tmp, "datos_hasta_corte")
    recortar_crudos(os.path.join(BASE_DIR, "datos_red"), recortados,
                    limite=datetime.combine(corte, datetime.min.time()))
    sal_corta = os.path.join(tmp, "pred_datos_hasta_corte.csv")
    sal_larga = os.path.join(tmp, "pred_datos_con_30_dias_mas.csv")
    try:
        predecir(recortados, corte, sal_corta)
        predecir(os.path.join(BASE_DIR, "datos_red"), corte, sal_larga)
    finally:
        predecir(os.path.join(BASE_DIR, "datos_red"), CORTES["C"],
                 os.path.join(BASE_DIR, "predicciones", f"predicciones_{CORTES['C'].isoformat()}.csv"))

    with open(sal_corta, "rb") as f1, open(sal_larga, "rb") as f2:
        identicos = f1.read() == f2.read()
    a, b = pd.read_csv(sal_corta), pd.read_csv(sal_larga)
    m = a.merge(b, on="unidad_id", how="outer", suffixes=("_corto", "_largo"), indicator=True)
    distintas = int(((m["_merge"] != "both") | (m["puntaje_corto"] != m["puntaje_largo"])
                     | (m["contactar_corto"] != m["contactar_largo"])
                     | (m["tarjetas_corto"] != m["tarjetas_largo"])).sum())
    resultado = {"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "corte": corte.isoformat(),
                 "filas_datos_hasta_corte": len(a), "filas_datos_con_30_dias_mas": len(b),
                 "filas_distintas": distintas, "archivos_identicos_byte_a_byte": identicos}
    with open(os.path.join(DOCS_P2, "prueba_invariancia.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
