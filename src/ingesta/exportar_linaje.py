"""Genera docs/linaje.md (grafo mermaid) a partir del manifest de dbt.

Requiere haber corrido antes `dbt run` o `dbt docs generate` en dbt_project/.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(BASE_DIR, "dbt_project", "target", "manifest.json")
SALIDA = os.path.join(BASE_DIR, "docs", "linaje.md")


def nombre(unique_id):
    return unique_id.split(".")[-1] if unique_id.startswith(("model.", "source.")) else None


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    nodos = {**manifest["nodes"], **manifest["sources"]}
    aristas = []
    for hijo, padres in manifest["parent_map"].items():
        if nombre(hijo) is None:
            continue
        for padre in padres:
            if nombre(padre) is not None:
                aristas.append((padre, hijo))

    def etiqueta(uid):
        n = nodos[uid]
        if uid.startswith("source."):
            return f"bronze.{n['name']}"
        return n["name"]

    ids = {}
    def nid(uid):
        if uid not in ids:
            ids[uid] = f"n{len(ids)}"
        return ids[uid]

    lineas = ["# Linaje de datos", "",
              "Generado con src/ingesta/exportar_linaje.py a partir del manifest de dbt.",
              "Cada modelo de gold se puede seguir hacia atras hasta el archivo crudo en bronze.",
              "Para verlo de forma interactiva: `dbt docs generate` y `dbt docs serve` dentro de dbt_project.",
              "", "```mermaid", "graph LR"]
    for padre, hijo in sorted(set(aristas)):
        lineas.append(f'    {nid(padre)}["{etiqueta(padre)}"] --> {nid(hijo)}["{etiqueta(hijo)}"]')
    lineas.append("```")

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"Linaje escrito en {SALIDA} ({len(set(aristas))} relaciones)")


if __name__ == "__main__":
    main()
