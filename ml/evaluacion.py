"""Piezas comunes de modelado: datos por corte, folds fijos y validacion cruzada.

Todos los modelos (baselines, logisticas y ensembles) se evaluan con los
mismos 5 folds estratificados del corte A, guardados en
ml/salidas/folds_A.csv, para que la comparacion sea justa.
"""
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.config import N_FOLDS, SALIDAS, SEMILLA
from ml.features import COLUMNAS_CATEGORICAS, COLUMNAS_FEATURES, COLUMNAS_NUMERICAS

RUTA_FEATURES = os.path.join(SALIDAS, "features_cortes.parquet")
RUTA_FOLDS = os.path.join(SALIDAS, "folds_A.csv")


def cargar_corte(nombre):
    df = pd.read_parquet(RUTA_FEATURES)
    df = df[df["corte"] == nombre].sort_values("unidad_id").reset_index(drop=True)
    return df


def folds_corte_a(df_a):
    """Asigna (o lee) el fold de cada unidad del corte A. Siempre los mismos."""
    if os.path.exists(RUTA_FOLDS):
        folds = pd.read_csv(RUTA_FOLDS)
        mapa = dict(zip(folds["unidad_id"], folds["fold"]))
        if len(mapa) == len(df_a) and df_a["unidad_id"].isin(mapa.keys()).all():
            return df_a["unidad_id"].map(mapa).to_numpy()
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA)
    fold = np.empty(len(df_a), dtype=int)
    for i, (_, val) in enumerate(skf.split(df_a, df_a["etiqueta"])):
        fold[val] = i
    pd.DataFrame({"unidad_id": df_a["unidad_id"], "fold": fold}).to_csv(RUTA_FOLDS, index=False)
    return fold


def preprocesador():
    return ColumnTransformer([
        ("num", StandardScaler(), COLUMNAS_NUMERICAS),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), COLUMNAS_CATEGORICAS),
    ])


def metricas(y, p):
    return {"pr_auc": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p)}


def validar(construir_modelo, df, fold, puntaje_fijo=None):
    """Valida con los folds dados.

    construir_modelo: funcion que devuelve un estimador nuevo (con
    predict_proba). puntaje_fijo: en vez de modelo, funcion df -> puntaje
    (para los baselines que no se entrenan).
    Devuelve las metricas por fold (entrenamiento y validacion) y las
    predicciones fuera de fold.
    """
    X = df[COLUMNAS_FEATURES]
    y = df["etiqueta"].astype(int).to_numpy()
    oof = np.zeros(len(df))
    filas = []
    for k in sorted(np.unique(fold)):
        tr, va = fold != k, fold == k
        if puntaje_fijo is not None:
            p_tr, p_va = puntaje_fijo(df[tr]), puntaje_fijo(df[va])
        else:
            modelo = construir_modelo()
            modelo.fit(X[tr], y[tr])
            p_tr = modelo.predict_proba(X[tr])[:, 1]
            p_va = modelo.predict_proba(X[va])[:, 1]
        oof[va] = p_va
        m_tr, m_va = metricas(y[tr], p_tr), metricas(y[va], p_va)
        filas.append({"fold": int(k), "pr_auc_train": m_tr["pr_auc"], "pr_auc_val": m_va["pr_auc"],
                      "roc_auc_train": m_tr["roc_auc"], "roc_auc_val": m_va["roc_auc"]})
    return pd.DataFrame(filas), oof


def resumen(nombre, por_fold):
    return {
        "modelo": nombre,
        "pr_auc_val_media": por_fold["pr_auc_val"].mean(),
        "pr_auc_val_std": por_fold["pr_auc_val"].std(ddof=1),
        "pr_auc_train_media": por_fold["pr_auc_train"].mean(),
        "roc_auc_val_media": por_fold["roc_auc_val"].mean(),
        "roc_auc_val_std": por_fold["roc_auc_val"].std(ddof=1),
    }
