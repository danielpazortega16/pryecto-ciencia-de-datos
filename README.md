# Agencia Metropolitana de Transporte

Proyecto 1: plataforma de datos de la red (más abajo). Proyecto 2: ¿quién
deja de usar la red? Un modelo que estima la probabilidad de que una
persona deje de viajar en los próximos 30 días y decide a quién contactar.
El estado final del Proyecto 1 quedó en la etiqueta `proyecto-1`.

## Proyecto 2: cómo correrlo

Requisitos: Python 3.13 y las versiones fijas de `requirements.txt`:

```bash
pip install -r requirements.txt
```

Comando único desde un entorno vacío. Vacía el lake (`bronze/`), el
warehouse y los artefactos de dbt, carga `datos_red/` y deja las features
de los cortes A, B y C:

```bash
python orquestacion/flow_prefect.py --desde-cero
```

Predicciones para una fecha de corte, con el modelo guardado en
`modelos/` (no reentrena):

```bash
python predecir.py --datos datos_red --fecha-corte 2026-08-30
```

El resto de pasos, en el orden en que se corrieron (cada uno deja sus
salidas en `docs/proyecto2/`):

```bash
python -m ml.prueba_recorte --nivel silver
python -m ml.prueba_recorte --nivel crudo
python -m ml.costo_unidad
python -m ml.fase1_modelos
python -m ml.fase2_ensemble
python -m ml.umbral --modelo "HistGradientBoosting"
python -m ml.evaluar_test_b --modelo hgb
python -m ml.segmentos --k 5
```

La semilla es 42 en todo el proyecto (`ml/config.py`). Los informes están
en `docs/proyecto2/` y la bitácora de corridas en
`docs/proyecto2/bitacora.md`.

## Proyecto 1

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
- `tableau/`: el tablero (tablero_agencia.twbx) y los CSV que lee.
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
ha visto el repo. El razonamiento detrás de cada decisión (grano, identidad
del usuario, zona conformada, cuarentena, idempotencia) está en
docs/decisiones.md, y las cifras medidas en docs/metricas.md.

Arquitectura y modelo: docs/diagrama_modelo.md, docs/matriz_bus.md,
docs/ddl_gold.sql y docs/linaje.md (de cada tabla de gold hasta el archivo crudo).

Gobernanza y seguridad: docs/diccionario_datos.md,
docs/definiciones_oficiales.md y docs/seguridad.md.

Consumo: docs/recomendacion.md (la recomendación para la Agencia),
docs/features.md (tabla de features desde Silver), docs/tablero.md y la
carpeta tableau/ con el tablero y los CSV que lee.

## Variables de entorno

PSEUDO_SALT es la sal con que se seudonimiza la tarjeta. Si no existe se
usa una de desarrollo; para una corrida real hay que definirla (ver
.env.example). No se sube al repositorio.

## Verificar idempotencia

```bash
python src/ingesta/verificar_idempotencia.py
```

Corre ingesta y dbt dos veces y compara el conteo de las tablas de silver,
gold y features. Debe terminar diciendo que los conteos son idénticos.

## Tablero

El tablero está en tableau/tablero_agencia.twbx y se explica en
docs/tablero.md. Se abre con Tableau Public o Tableau Desktop.
