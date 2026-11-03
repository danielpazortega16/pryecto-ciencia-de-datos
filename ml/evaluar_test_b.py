"""Fase 2, seccion 2.2 (segunda parte): entrenamiento final y test UNICO en B.

Entrena el modelo elegido con todo el corte A, lo guarda con su version y
lo evalua una sola vez con la etiqueta del corte B. Se niega a correr si ya
existe docs/proyecto2/test_b.json (la evaluacion ya se hizo) o si hay
cambios sin commit (la evaluacion tiene que quedar atada a un commit).

Uso:
    python -m ml.evaluar_test_b --modelo hgb
"""
import argparse
import json
import os
import subprocess
import time
from datetime import datetime

import joblib
import numpy as np
import sklearn

from ml.config import BASE_DIR, DOCS_P2, MODELOS
from ml.evaluacion import cargar_corte, metricas
from ml.features import COLUMNAS_FEATURES
from ml.umbral import ganancia

VERSION = "v1"
RUTA_TEST = os.path.join(DOCS_P2, "test_b.json")


def fabrica(nombre):
    if nombre == "hgb":
        from ml.fase2_ensemble import boosting
        return boosting()
    if nombre == "logistica":
        from ml.fase1_modelos import CASTIGOS, logistica
        with open(os.path.join(DOCS_P2, "fase1_resumen.json"), encoding="utf-8") as f:
            lam = json.load(f)["lambdas_elegidos"]["L2"]
        return logistica(CASTIGOS["L2"], lam)
    raise ValueError(nombre)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", choices=["hgb", "logistica"], required=True)
    args = parser.parse_args()

    if os.path.exists(RUTA_TEST):
        raise SystemExit("El test en B ya se hizo (docs/proyecto2/test_b.json). No se repite.")
    estado = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True).stdout
    if estado.strip():
        raise SystemExit("Hay cambios sin commit. La evaluacion en B tiene que quedar atada a un commit.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE_DIR, capture_output=True, text=True).stdout.strip()

    with open(os.path.join(DOCS_P2, "umbral.json"), encoding="utf-8") as f:
        umbral = float(json.load(f)["elegido"]["umbral"])

    a, b = cargar_corte("A"), cargar_corte("B")
    t0 = time.perf_counter()
    modelo = fabrica(args.modelo).fit(a[COLUMNAS_FEATURES], a["etiqueta"].astype(int))
    seg_entrenamiento = time.perf_counter() - t0

    ruta_modelo = os.path.join(MODELOS, f"modelo_abandono_{VERSION}.joblib")
    joblib.dump({"version": VERSION, "tipo": args.modelo, "pipeline": modelo, "umbral": umbral,
                 "columnas": COLUMNAS_FEATURES, "entrenado_con": "corte A (2026-07-01)",
                 "commit": commit, "sklearn": sklearn.__version__}, ruta_modelo)

    yb = b["etiqueta"].astype(int).to_numpy()
    pb = modelo.predict_proba(b[COLUMNAS_FEATURES])[:, 1]
    m = metricas(yb, pb)
    base_tasa = metricas(yb, np.full(len(yb), a["etiqueta"].mean()))
    base_rec = metricas(yb, b["dias_desde_ultimo_viaje"].to_numpy())
    g = ganancia(yb, pb, umbral)
    vn = int(((yb == 0) & (pb < umbral)).sum())

    resultado = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "commit": commit,
        "modelo": args.modelo,
        "archivo_modelo": os.path.relpath(ruta_modelo, BASE_DIR).replace("\\", "/"),
        "umbral": umbral,
        "poblacion_b": int(len(yb)), "positivos_b": int(yb.sum()),
        "pr_auc_b": m["pr_auc"], "roc_auc_b": m["roc_auc"],
        "baseline_tasa_pr_auc_b": base_tasa["pr_auc"],
        "baseline_dias_sin_viajar_pr_auc_b": base_rec["pr_auc"],
        "matriz_confusion": {"vp": g["vp"], "fp": g["fp"], "fn": g["fn"], "vn": vn},
        "precision": g["precision"], "recall": g["recall"], "contactados": g["contactados"],
        "ganancia_q": g["ganancia_q"],
        "segundos_entrenamiento": round(seg_entrenamiento, 1),
    }
    with open(RUTA_TEST, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DOCS_P2, "bitacora.md"), "a", encoding="utf-8") as f:
        f.write(f"\n## {resultado['fecha']} - Evaluacion unica en el corte B\n\n"
                f"Commit {commit}. Modelo {args.modelo} entrenado con todo el corte A, umbral {umbral}. "
                f"PR-AUC en B {m['pr_auc']:.4f} (baseline tasa {base_tasa['pr_auc']:.4f}, "
                f"baseline dias sin viajar {base_rec['pr_auc']:.4f}). Ganancia Q{g['ganancia_q']:,.0f}. "
                f"No se ajusto nada despues de ver este resultado.\n")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
