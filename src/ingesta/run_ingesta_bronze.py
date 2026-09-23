"""Corre las tres vias de ingesta y deja la tabla de conteos por archivo (1.1)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingesta_batch  # noqa: E402
import ingesta_streaming  # noqa: E402
import ingesta_transurbano  # noqa: E402
import ingesta_cdc  # noqa: E402
from comun import BASE_DIR  # noqa: E402


def main():
    conteos = {}
    conteos.update(ingesta_batch.main())
    conteos.update(ingesta_streaming.main())
    conteos["tu_transacciones"] = ingesta_transurbano.main()
    conteos["cdc_padron_usuarios"] = ingesta_cdc.main()

    print("\n=== Tabla de conteos por archivo (Bronze) ===")
    ancho = max(len(k) for k in conteos)
    for fuente, n in conteos.items():
        print(f"  {fuente.ljust(ancho)} : {n}")

    out_path = os.path.join(BASE_DIR, "docs", "conteos_bronze.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(conteos, f, indent=2, ensure_ascii=False)
    print(f"\nGuardado en {out_path}")
    return conteos


if __name__ == "__main__":
    main()
