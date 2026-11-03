"""Fase 2, seccion 2.1: ensembles, sesgo-varianza e importancia por permutacion.

Usa los mismos 5 folds del corte A que la Fase 1. Compara contra la mejor
logistica con la metrica de entrenamiento y de validacion.

Uso:
    python -m ml.fase2_ensemble
"""
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.config import DOCS_P2, SALIDAS, SEMILLA
from ml.evaluacion import cargar_corte, folds_corte_a, resumen, validar
from ml.fase1_modelos import CASTIGOS, logistica
from ml.features import COLUMNAS_CATEGORICAS, COLUMNAS_FEATURES, COLUMNAS_NUMERICAS


def _prep_arboles():
    return ColumnTransformer([
        ("num", "passthrough", COLUMNAS_NUMERICAS),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), COLUMNAS_CATEGORICAS),
    ])


def boosting():
    return Pipeline([
        ("prep", _prep_arboles()),
        ("clf", HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_leaf_nodes=31,
                                               min_samples_leaf=100, l2_regularization=1.0,
                                               early_stopping=False, random_state=SEMILLA)),
    ])


def bosque():
    return Pipeline([
        ("prep", _prep_arboles()),
        ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=20, max_features="sqrt",
                                       n_jobs=-1, random_state=SEMILLA)),
    ])


def main():
    inicio = time.perf_counter()
    df = cargar_corte("A")
    fold = folds_corte_a(df)
    with open(os.path.join(DOCS_P2, "fase1_resumen.json"), encoding="utf-8") as f:
        f1 = json.load(f)
    lam_l2 = f1["lambdas_elegidos"]["L2"]

    modelos = {
        f"Logistica L2, lambda={lam_l2:.3g}": lambda: logistica(CASTIGOS["L2"], lam_l2),
        "HistGradientBoosting": boosting,
        "Random Forest": bosque,
    }
    tabla, oofs, tiempos = [], {}, {}
    for nombre, fabrica in modelos.items():
        t0 = time.perf_counter()
        pf, oof = validar(fabrica, df, fold)
        tiempos[nombre] = round(time.perf_counter() - t0, 1)
        oofs[nombre] = oof
        fila = resumen(nombre, pf)
        fila["brecha_train_val"] = fila["pr_auc_train_media"] - fila["pr_auc_val_media"]
        fila["segundos_cv"] = tiempos[nombre]
        tabla.append(fila)
    tabla = pd.DataFrame(tabla)
    tabla.to_csv(os.path.join(DOCS_P2, "tabla_modelos_fase2.csv"), index=False)
    pd.DataFrame({"unidad_id": df["unidad_id"], "fold": fold, "etiqueta": df["etiqueta"], **oofs}).to_parquet(
        os.path.join(SALIDAS, "oof_fase2.parquet"), index=False)

    # Importancia por permutacion en el fold de validacion (no en entrenamiento),
    # promediada en los 5 folds, para el boosting.
    X, y = df[COLUMNAS_FEATURES], df["etiqueta"].astype(int).to_numpy()
    imps = []
    for k in range(5):
        tr, va = fold != k, fold == k
        m = boosting().fit(X[tr], y[tr])
        r = permutation_importance(m, X[va], y[va], scoring="average_precision", n_repeats=5,
                                   random_state=SEMILLA, n_jobs=-1)
        imps.append(r.importances_mean)
    imp = pd.DataFrame({"feature": COLUMNAS_FEATURES, "importancia_media": np.mean(imps, axis=0),
                        "importancia_std_entre_folds": np.std(imps, axis=0, ddof=1)})
    imp = imp.sort_values("importancia_media", ascending=False)
    imp.to_csv(os.path.join(DOCS_P2, "importancia_permutacion.csv"), index=False)

    print(tabla.to_string(index=False))
    print(imp.head(10).to_string(index=False))
    print("segundos totales", round(time.perf_counter() - inicio, 1))


if __name__ == "__main__":
    main()
