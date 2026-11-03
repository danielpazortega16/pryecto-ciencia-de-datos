"""Fase 1, seccion 1.4: lineas base y regresion logistica regularizada.

Solo usa el corte A, con los 5 folds fijos. No toca la etiqueta del corte B.

  Baseline 1: a todos la tasa positiva del corte A.
  Baseline 2: una sola feature como puntaje, dias_desde_ultimo_viaje (quien
              lleva mas dias sin viajar queda con mas riesgo).
  Baseline 3: otra feature, menos viajes en las 4 semanas = mas riesgo.
  Logistica con castigo L2, L1 y Elastic Net, barriendo lambda (C = 1/lambda).

Uso:
    python -m ml.fase1_modelos
"""
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.config import DOCS_P2, SALIDAS, SEMILLA
from ml.evaluacion import cargar_corte, folds_corte_a, preprocesador, resumen, validar

LAMBDAS = np.logspace(-3, 3, 13)
CASTIGOS = {"L2": 0.0, "L1": 1.0, "Elastic Net (l1_ratio=0.5)": 0.5}


def logistica(l1_ratio, lam):
    solver = "lbfgs" if l1_ratio == 0.0 else "saga"
    return Pipeline([
        ("prep", preprocesador()),
        ("clf", LogisticRegression(C=1.0 / lam, l1_ratio=l1_ratio, solver=solver,
                                   max_iter=3000, tol=1e-4, random_state=SEMILLA)),
    ])


def main():
    inicio = time.perf_counter()
    df = cargar_corte("A")
    fold = folds_corte_a(df)
    tasa = df["etiqueta"].mean()

    tabla = []
    oofs = {}
    pf, oofs["Baseline: tasa del corte A"] = validar(None, df, fold, puntaje_fijo=lambda d: np.full(len(d), tasa))
    tabla.append(resumen("Baseline: tasa del corte A", pf))
    pf, oofs["Baseline: dias desde el ultimo viaje"] = validar(None, df, fold, puntaje_fijo=lambda d: d["dias_desde_ultimo_viaje"].to_numpy())
    tabla.append(resumen("Baseline: dias desde el ultimo viaje", pf))
    pf, oofs["Baseline: menos viajes en 28 dias"] = validar(None, df, fold, puntaje_fijo=lambda d: -d["viajes_28d"].to_numpy())
    tabla.append(resumen("Baseline: menos viajes en 28 dias", pf))

    curvas = []
    mejores = {}
    for nombre, ratio in CASTIGOS.items():
        for lam in LAMBDAS:
            pf, _ = validar(lambda r=ratio, l=lam: logistica(r, l), df, fold)
            curvas.append({"castigo": nombre, "lambda": lam, "pr_auc_media": pf["pr_auc_val"].mean(),
                           "pr_auc_std": pf["pr_auc_val"].std(ddof=1)})
        c = pd.DataFrame([x for x in curvas if x["castigo"] == nombre])
        mejor = c.loc[c["pr_auc_media"].idxmax()]
        mejores[nombre] = float(mejor["lambda"])
        pf, oof = validar(lambda r=ratio, l=mejor["lambda"]: logistica(r, l), df, fold)
        oofs[f"Logistica {nombre}"] = oof
        fila = resumen(f"Logistica {nombre}, lambda={mejor['lambda']:.3g}", pf)
        tabla.append(fila)

    curvas = pd.DataFrame(curvas)
    curvas.to_csv(os.path.join(DOCS_P2, "logistica_curva_lambda.csv"), index=False)
    tabla = pd.DataFrame(tabla)
    tabla.to_csv(os.path.join(DOCS_P2, "tabla_modelos_fase1.csv"), index=False)
    pd.DataFrame({"unidad_id": df["unidad_id"], "fold": fold, "etiqueta": df["etiqueta"], **oofs}).to_parquet(
        os.path.join(SALIDAS, "oof_fase1.parquet"), index=False)

    graficar(curvas, mejores, tasa)

    # Coeficientes del mejor castigo, ajustado con todo el corte A (solo para
    # interpretar; la evaluacion ya se hizo por validacion cruzada).
    mejor_nombre = tabla[tabla["modelo"].str.startswith("Logistica")].sort_values("pr_auc_val_media").iloc[-1]["modelo"]
    clave = next(k for k in CASTIGOS if k in mejor_nombre)
    modelo = logistica(CASTIGOS[clave], mejores[clave]).fit(df[cargar_columnas()], df["etiqueta"].astype(int))
    nombres = modelo.named_steps["prep"].get_feature_names_out()
    coefs = pd.DataFrame({"feature": nombres, "coeficiente": modelo.named_steps["clf"].coef_[0]})
    coefs = coefs.sort_values("coeficiente", ascending=False)
    coefs.to_csv(os.path.join(DOCS_P2, "logistica_coeficientes.csv"), index=False)

    resumen_json = {"tasa_corte_a": tasa, "lambdas_elegidos": mejores, "mejor_logistica": mejor_nombre,
                    "segundos": round(time.perf_counter() - inicio, 1)}
    with open(os.path.join(DOCS_P2, "fase1_resumen.json"), "w", encoding="utf-8") as f:
        json.dump(resumen_json, f, indent=2, ensure_ascii=False)
    print(tabla.to_string(index=False))
    print(coefs.head(8).to_string(index=False))
    print(resumen_json)


def graficar(curvas, mejores, tasa):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for nombre, c in curvas.groupby("castigo"):
        linea = ax.errorbar(c["lambda"], c["pr_auc_media"], yerr=c["pr_auc_std"], marker="o", ms=3,
                            capsize=2, label=f"{nombre} (elegido lambda={mejores[nombre]:.3g})")
        ax.axvline(mejores[nombre], ls=":", lw=1, color=linea[0].get_color())
    ax.set_xscale("log")
    ax.set_xlabel("lambda (castigo de regularizacion, C = 1/lambda)")
    ax.set_ylabel("PR-AUC en validacion (media y desv. de 5 folds)")
    ax.set_title(f"Logistica: PR-AUC contra lambda (baseline tasa del corte A = {tasa:.3f}, fuera del eje)")
    ax.title.set_fontsize(9)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS_P2, "logistica_pr_auc_vs_lambda.png"), dpi=130)


def cargar_columnas():
    from ml.features import COLUMNAS_FEATURES
    return COLUMNAS_FEATURES


if __name__ == "__main__":
    import sys
    if "--solo-grafica" in sys.argv:
        c = pd.read_csv(os.path.join(DOCS_P2, "logistica_curva_lambda.csv"))
        with open(os.path.join(DOCS_P2, "fase1_resumen.json"), encoding="utf-8") as f:
            r = json.load(f)
        graficar(c, r["lambdas_elegidos"], r["tasa_corte_a"])
    else:
        main()
