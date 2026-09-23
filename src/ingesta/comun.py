"""Utilidades compartidas por los scripts de ingesta a Bronze."""
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATOS_RED = os.path.join(BASE_DIR, "datos_red")
BRONZE_DIR = os.path.join(BASE_DIR, "bronze")


def ahora_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def ruta_particion_bronze(fuente: str, fecha_ingesta: str) -> str:
    """Carpeta particionada por fecha de ingesta, una por fuente (lake)."""
    carpeta = os.path.join(BRONZE_DIR, fuente, f"fecha_ingesta={fecha_ingesta}")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta
