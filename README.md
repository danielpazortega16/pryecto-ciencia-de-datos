# Agencia Metropolitana de Transporte — Proyecto 1 (Ciencia de Datos)

Pipeline Bronze → Silver → Gold para integrar los cuatro operadores de
transporte de la ciudad (Transmetro, Transurbano, MetroRiel, Aerómetro),
que hoy no comparten formato, llave de usuario, moneda ni definición de
zona. Ver `docs/decisiones.md` para el razonamiento detrás de cada
decisión de arquitectura.

## Requisitos

- Python 3.11+ (probado con 3.13)
- Paquetes: `pip install duckdb dbt-duckdb prefect`
- No requiere Docker ni Postgres para correr esta Fase 1 (ver decisión de
  sustitución de Kafka en `docs/decisiones.md` §2).

## Estructura

```
generar_red_metropolitana.py   # generador oficial del curso
datos_red/                     # 9 archivos generados (CSV/JSONL), no versionados
src/ingesta/                   # scripts de ingesta a Bronze (streaming/batch/CDC)
bronze/                        # lake Parquet particionado por fecha_ingesta, no versionado
dbt_project/                   # staging -> silver -> gold
warehouse.duckdb               # Staging/Silver/Gold, no versionado
orquestacion/flow_prefect.py   # orquesta todo el flujo, idempotente
docs/                          # decisiones, métricas, DDL, matriz del bus
```

## Cómo correr el flujo completo

```bash
# 1. Generar los datos (si no existen en datos_red/)
python generar_red_metropolitana.py

# 2. Correr todo: ingesta a Bronze -> dbt run -> dbt test
python orquestacion/flow_prefect.py
```

Esto es **idempotente**: se puede correr las veces que se quiera el mismo
día sin duplicar nada (Bronze sobreescribe la partición del día, Silver y
Gold son tablas recalculadas por completo). Evidencia de dos corridas con
conteos idénticos: `docs/evidencia_idempotencia.json`.

### Correr manualmente por partes

```bash
# Solo ingesta
python src/ingesta/run_ingesta_bronze.py

# Solo transformaciones (staging/silver/gold), desde dbt_project/
export PROJECT_ROOT="/ruta/absoluta/al/proyecto"   # con "/" incluso en Windows
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .

# Regenerar el DDL de Gold
python src/ingesta/exportar_ddl_gold.py
```

`PROJECT_ROOT` debe ser la ruta absoluta del proyecto (con `/` como
separador, DuckDB lo acepta también en Windows) — la usan
`dbt_project/models/staging/_sources.yml` y `dbt_project/profiles.yml`
para ubicar `bronze/` y `warehouse.duckdb` sin depender del directorio
desde el que se invoque `dbt`.

## Consultar el resultado

```python
import duckdb
con = duckdb.connect("warehouse.duckdb", read_only=True)
con.execute("select * from main_gold.fact_abordaje limit 10").fetchall()
```

## Documentación

- `docs/decisiones.md` — grano, identidad de usuario, zona conformada,
  criterios de cuarentena, vía de ingesta por fuente.
- `docs/matriz_bus.md` — matriz del bus de procesos.
- `docs/metricas.md` — volumen, calidad, CDC, rendimiento, idempotencia,
  cobertura (cifras medidas, no supuestas).
- `docs/ddl_gold.sql` — DDL de la capa Gold.

## Pendiente (fuera de alcance de Fase 1)

Tablero en Tableau, recomendación de negocio, tabla de features para
ciencia de datos, gobernanza formal (diccionario de datos, definiciones
oficiales con dueño) y seudonimización antes de Gold — ver
`docs/decisiones.md` §7.
