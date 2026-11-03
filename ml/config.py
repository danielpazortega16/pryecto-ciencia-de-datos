"""Parametros fijos del Proyecto 2."""
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")
SALIDAS = os.path.join(BASE_DIR, "ml", "salidas")
MODELOS = os.path.join(BASE_DIR, "modelos")
DOCS_P2 = os.path.join(BASE_DIR, "docs", "proyecto2")

CORTES = {
    "A": date(2026, 7, 1),
    "B": date(2026, 7, 31),
    "C": date(2026, 8, 30),
}
VENTANA_DIAS = 28
HORIZONTE_DIAS = 30
MIN_VIAJES_POBLACION = 2
SEMILLA = 42
N_FOLDS = 5

# Escenario de costos de la Agencia (enunciado 2.2).
COSTO_CONTACTO = 5.0
TASA_RETENCION = 0.25
VALOR_RETENIDO = 60.0

for carpeta in (SALIDAS, MODELOS, DOCS_P2):
    os.makedirs(carpeta, exist_ok=True)
