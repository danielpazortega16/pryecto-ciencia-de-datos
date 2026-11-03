"""Fase 2, seccion 2.2 (primera parte): umbral segun el escenario de costos.

Escenario: contactar cuesta Q5; si el usuario se iba a ir, la campana lo
retiene en el 25% de los casos; un usuario retenido vale Q60.

Ganancia esperada de contactar a un usuario que se iba a ir:
    0.25 x Q60 - Q5 = Q15 - Q5 = Q10
Ganancia de contactar a uno que no se iba a ir:
    -Q5
Ganancia de contactar a un grupo:
    G = 10 x VP - 5 x FP      (VP: contactados que se iban, FP: contactados que no)
Con probabilidades bien calibradas conviene contactar si
    p x 15 - 5 > 0  ->  p > 5 / 15 = 1/3
El umbral se elige maximizando G sobre las predicciones fuera de fold del
corte A (validacion cruzada), no sobre el corte B.

Uso:
    python -m ml.umbral --modelo "HistGradientBoosting"
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ml.config import COSTO_CONTACTO, DOCS_P2, SALIDAS, TASA_RETENCION, VALOR_RETENIDO

GANANCIA_VP = TASA_RETENCION * VALOR_RETENIDO - COSTO_CONTACTO  # 10
GANANCIA_FP = -COSTO_CONTACTO                                    # -5
UMBRAL_TEORICO = COSTO_CONTACTO / (TASA_RETENCION * VALOR_RETENIDO)  # 1/3


def ganancia(y, p, umbral):
    contactar = p >= umbral
    vp = int(((y == 1) & contactar).sum())
    fp = int(((y == 0) & contactar).sum())
    fn = int(((y == 1) & ~contactar).sum())
    return {"umbral": umbral, "contactados": vp + fp, "vp": vp, "fp": fp, "fn": fn,
            "precision": vp / (vp + fp) if vp + fp else 0.0,
            "recall": vp / (vp + fn) if vp + fn else 0.0,
            "ganancia_q": GANANCIA_VP * vp + GANANCIA_FP * fp}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", required=True, help="columna del modelo en oof_fase2.parquet")
    args = parser.parse_args()
    oof = pd.read_parquet(os.path.join(SALIDAS, "oof_fase2.parquet"))
    y, p = oof["etiqueta"].astype(int).to_numpy(), oof[args.modelo].to_numpy()

    umbrales = np.round(np.arange(0.01, 0.991, 0.005), 3)
    curva = pd.DataFrame([ganancia(y, p, u) for u in umbrales])
    mejor = curva.loc[curva["ganancia_q"].idxmax()].to_dict()
    teorico = ganancia(y, p, UMBRAL_TEORICO)
    todos = ganancia(y, p, 0.0)
    curva.to_csv(os.path.join(DOCS_P2, "curva_ganancia.csv"), index=False)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(curva["umbral"], curva["ganancia_q"], lw=1.8)
    ax.axvline(mejor["umbral"], color="tab:red", ls="--", lw=1,
               label=f"umbral elegido {mejor['umbral']:.3f}: Q{mejor['ganancia_q']:,.0f}")
    ax.axvline(UMBRAL_TEORICO, color="grey", ls=":", lw=1, label="umbral teorico 1/3")
    ax.axhline(todos["ganancia_q"], color="tab:orange", ls=":", lw=1,
               label=f"contactar a todos: Q{todos['ganancia_q']:,.0f}")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel("umbral (probabilidad a partir de la cual se contacta)")
    ax.set_ylabel("ganancia en quetzales (corte A, fuera de fold)")
    ax.set_title(f"Ganancia contra umbral - {args.modelo}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS_P2, "curva_ganancia.png"), dpi=130)

    salida = {"modelo": args.modelo, "formula": "G = 10 x VP - 5 x FP",
              "umbral_teorico": UMBRAL_TEORICO, "elegido": mejor, "en_umbral_teorico": teorico,
              "contactar_a_todos": todos, "poblacion_a": int(len(y)), "positivos_a": int(y.sum())}
    with open(os.path.join(DOCS_P2, "umbral.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False, default=float)
    print(json.dumps(salida, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
