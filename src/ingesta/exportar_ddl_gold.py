"""Genera el DDL de la capa Gold a partir del catalogo de DuckDB (1.4)."""
import os
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")
OUT_PATH = os.path.join(BASE_DIR, "docs", "ddl_gold.sql")

TIPOS = {
    "BIGINT": "BIGINT", "INTEGER": "INTEGER", "VARCHAR": "VARCHAR",
    "DOUBLE": "DOUBLE", "BOOLEAN": "BOOLEAN", "DATE": "DATE",
    "TIMESTAMP": "TIMESTAMP",
}


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    tablas = con.execute("""
        select table_name from information_schema.tables
        where table_schema = 'main_gold' order by table_name
    """).fetchall()

    lineas = ["-- DDL generado desde el catalogo de DuckDB (capa Gold)", ""]
    for (tabla,) in tablas:
        cols = con.execute(f"""
            select column_name, data_type
            from information_schema.columns
            where table_schema = 'main_gold' and table_name = '{tabla}'
            order by ordinal_position
        """).fetchall()
        lineas.append(f"CREATE TABLE main_gold.{tabla} (")
        col_defs = [f"    {c} {t}" for c, t in cols]
        lineas.append(",\n".join(col_defs))
        lineas.append(");\n")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"DDL escrito en {OUT_PATH}")
    con.close()


if __name__ == "__main__":
    main()
