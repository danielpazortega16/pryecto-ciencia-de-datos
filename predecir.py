"""Predicciones de abandono para una fecha de corte (2.4).

Carga los datos de la carpeta indicada con el pipeline del proyecto (desde
cero: vacia el lake y el warehouse), calcula las features del corte, carga
el modelo guardado (no lo reentrena) y escribe un CSV con:
    unidad_id, tarjetas, puntaje, contactar

Uso:
    python predecir.py --datos datos_red --fecha-corte 2026-08-30

Con --sin-pipeline usa el warehouse ya cargado (por ejemplo, si se acaba de
correr orquestacion/flow_prefect.py con esos mismos datos).
"""
import argparse
import os
import sys
import time
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
MODELO = os.path.join(BASE_DIR, "modelos", "modelo_abandono_v1.joblib")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datos", required=True, help="carpeta con los 9 archivos de la red")
    parser.add_argument("--fecha-corte", required=True, help="AAAA-MM-DD, 00:00 hora local")
    parser.add_argument("--salida", help="CSV de salida (por defecto predicciones/predicciones_<fecha>.csv)")
    parser.add_argument("--sin-pipeline", action="store_true")
    args = parser.parse_args()

    corte = date.fromisoformat(args.fecha_corte)
    datos = os.path.abspath(args.datos)
    if not os.path.isdir(datos):
        raise SystemExit(f"No existe la carpeta de datos: {datos}")
    os.environ["DATOS_RED_DIR"] = datos

    t0 = time.perf_counter()
    if not args.sin_pipeline:
        from orquestacion.flow_prefect import pipeline_completo
        pipeline_completo(desde_cero=True, con_features=False, reportes=False)
    t_pipeline = time.perf_counter() - t0

    import joblib
    from ml.features import conectar, construir, preparar_vistas

    t1 = time.perf_counter()
    paquete = joblib.load(MODELO)
    con = conectar()
    preparar_vistas(con)
    df = construir(con, corte, con_etiqueta=False)
    con.close()

    puntaje = paquete["pipeline"].predict_proba(df[paquete["columnas"]])[:, 1]
    df["puntaje"] = puntaje.round(6)
    df["contactar"] = (df["puntaje"] >= paquete["umbral"]).astype(int)
    salida = args.salida or os.path.join(BASE_DIR, "predicciones", f"predicciones_{corte.isoformat()}.csv")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    df.sort_values("unidad_id")[["unidad_id", "tarjetas", "puntaje", "contactar"]].to_csv(salida, index=False)
    t_pred = time.perf_counter() - t1

    print(f"Modelo {paquete['version']} ({paquete['tipo']}), umbral {paquete['umbral']}")
    print(f"Corte {corte}: {len(df):,} unidades, {int(df['contactar'].sum()):,} a contactar")
    print(f"Pipeline {t_pipeline:.1f} s, features y prediccion {t_pred:.1f} s")
    print(f"CSV: {salida}")


if __name__ == "__main__":
    main()
