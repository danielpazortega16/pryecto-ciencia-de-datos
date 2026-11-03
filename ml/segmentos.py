"""Fase 2, seccion 2.3: segmentacion con KMeans y PCA sobre el corte A.

Escala las features numericas (KMeans y PCA dependen de las distancias),
elige k con el codo y la silueta, proyecta en dos componentes y describe
cada segmento con medianas y tasa de abandono. La tasa de abandono por
segmento es descriptiva: no prueba que el segmento cause el abandono. El
segmento no se usa como feature del clasificador.

Uso:
    python -m ml.segmentos            (calcula k de 2 a 8 y deja las graficas)
    python -m ml.segmentos --k 4      (ajusta con el k elegido y describe)
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ml.config import DOCS_P2, SEMILLA
from ml.evaluacion import cargar_corte
from ml.features import COLUMNAS_NUMERICAS

MUESTRA_SILUETA = 15000


def datos():
    df = cargar_corte("A")
    X = StandardScaler().fit_transform(df[COLUMNAS_NUMERICAS])
    return df, X


def elegir_k():
    df, X = datos()
    rng = np.random.default_rng(SEMILLA)
    idx = rng.choice(len(X), size=min(MUESTRA_SILUETA, len(X)), replace=False)
    filas = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(X)
        sil = silhouette_score(X[idx], km.labels_[idx])
        filas.append({"k": k, "inercia": km.inertia_, "silueta": sil})
    t = pd.DataFrame(filas)
    t.to_csv(os.path.join(DOCS_P2, "kmeans_k.csv"), index=False)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
    a1.plot(t["k"], t["inercia"], marker="o")
    a1.set_title("Metodo del codo")
    a1.set_xlabel("k")
    a1.set_ylabel("inercia")
    a2.plot(t["k"], t["silueta"], marker="o", color="tab:green")
    a2.set_title("Silueta (muestra de 15,000)")
    a2.set_xlabel("k")
    a2.set_ylabel("silueta media")
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS_P2, "kmeans_codo_silueta.png"), dpi=130)
    print(t.to_string(index=False))


def describir(k):
    df, X = datos()
    km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(X)
    df["segmento"] = km.labels_
    pca = PCA(n_components=2, random_state=SEMILLA)
    Z = pca.fit_transform(X)
    var = pca.explained_variance_ratio_

    rng = np.random.default_rng(SEMILLA)
    idx = rng.choice(len(Z), size=min(12000, len(Z)), replace=False)
    fig, ax = plt.subplots(figsize=(6.8, 5))
    for s in range(k):
        m = df["segmento"].to_numpy()[idx] == s
        ax.scatter(Z[idx][m, 0], Z[idx][m, 1], s=4, alpha=0.5, label=f"segmento {s}")
    ax.set_xlabel(f"PC1 ({var[0]:.1%} de la varianza)")
    ax.set_ylabel(f"PC2 ({var[1]:.1%} de la varianza)")
    ax.set_title(f"Segmentos en dos componentes (datos escalados, k={k})")
    ax.legend(markerscale=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS_P2, "segmentos_pca.png"), dpi=130)

    principales = ["viajes_28d", "dias_activos_28d", "dias_desde_ultimo_viaje", "tendencia_14d",
                   "n_operadores", "prop_aerometro", "prop_metroriel", "prop_transurbano",
                   "prop_hora_pico", "prop_fin_de_semana", "tarifa_promedio"]
    tabla = df.groupby("segmento").agg(tamano=("unidad_id", "size"), tasa_abandono=("etiqueta", "mean"),
                                       **{c: (c, "median") for c in principales}).reset_index()
    tabla.to_csv(os.path.join(DOCS_P2, "segmentos_tabla.csv"), index=False)
    with open(os.path.join(DOCS_P2, "segmentos_resumen.json"), "w", encoding="utf-8") as f:
        json.dump({"k": k, "varianza_explicada_pc1": var[0], "varianza_explicada_pc2": var[1],
                   "varianza_explicada_total": float(var.sum())}, f, indent=2)
    pd.set_option("display.width", 220)
    print(tabla.to_string(index=False))
    print("varianza explicada", var, var.sum())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int)
    args = parser.parse_args()
    describir(args.k) if args.k else elegir_k()
