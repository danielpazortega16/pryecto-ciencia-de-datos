# Agencia Metropolitana de Transporte — Proyecto 1

Pipeline Bronze/Silver/Gold para integrar los cuatro operadores de
transporte de la ciudad (Transmetro, Transurbano, MetroRiel, Aerómetro),
que hoy no comparten formato, llave de usuario, moneda ni definición de
zona. El razonamiento detrás de cada decisión de arquitectura está en
docs/decisiones.md.

## Requisitos

Python 3.11 o superior, y las librerías duckdb, dbt-duckdb y prefect
(`pip install duckdb dbt-duckdb prefect`). No hace falta Docker ni
Postgres para esta fase; la decisión de sustituir Kafka está explicada en
docs/decisiones.md.

## Estructura

- `generar_red_metropolitana.py`: generador oficial del curso.
- `datos_red/`: los 9 archivos generados (CSV/JSONL). No se sube a git.
- `src/ingesta/`: scripts de ingesta a Bronze (streaming, batch, CDC).
- `bronze/`: lake en Parquet particionado por fecha de ingesta. No se sube a git.
- `dbt_project/`: modelos de staging, silver y gold.
- `warehouse.duckdb`: base de datos con staging/silver/gold. No se sube a git.
- `orquestacion/flow_prefect.py`: corre todo el flujo con Prefect.
- `docs/`: decisiones, métricas, DDL, matriz del bus, manual de usuario.

## Cómo correr el flujo completo

Primero se generan los datos si no existen todavía:

```bash
python generar_red_metropolitana.py
```

Y luego un solo comando corre la ingesta, las transformaciones y las
pruebas de calidad:

```bash
python orquestacion/flow_prefect.py
```

Se puede correr las veces que se quiera el mismo día sin duplicar nada.
Bronze sobreescribe la carga del día y Silver/Gold se recalculan
completos en cada corrida, así que es idempotente por construcción. La
evidencia de dos corridas con los mismos conteos está en
docs/evidencia_idempotencia.json.

Si se quiere correr por partes, la ingesta sola es
`python src/ingesta/run_ingesta_bronze.py`, y las transformaciones se
corren desde `dbt_project/` con `dbt run --profiles-dir .` (hay que
exportar antes la variable `PROJECT_ROOT` con la ruta absoluta del
proyecto, usando `/` como separador aunque sea Windows, porque de ahí
toman la ruta tanto `models/staging/_sources.yml` como `profiles.yml`
para encontrar `bronze/` y `warehouse.duckdb` sin depender del directorio
desde el que se invoque dbt).

## Consultar el resultado

```python
import duckdb
con = duckdb.connect("warehouse.duckdb", read_only=True)
con.execute("select * from main_gold.fact_abordaje limit 10").fetchall()
```

## Documentación

En docs/MANUAL_USUARIO.md está la guía paso a paso para alguien que nunca
ha visto el repo. docs/decisiones.md explica el grano de las tablas de
hechos, cómo se resolvió la identidad del usuario, la zona conformada y
los criterios de cuarentena. docs/matriz_bus.md tiene la matriz del bus
de procesos, docs/metricas.md las cifras medidas de volumen, calidad, CDC,
rendimiento e idempotencia, y docs/ddl_gold.sql el DDL de la capa gold.

## Qué falta

El tablero en Tableau, la recomendación de negocio, la tabla de features
y la gobernanza formal (diccionario de datos, definiciones oficiales,
seudonimización antes de gold) quedaron fuera del alcance de esta fase;
están anotados en docs/decisiones.md.
