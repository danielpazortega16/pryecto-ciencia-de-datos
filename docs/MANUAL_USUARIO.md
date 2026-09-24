# Manual de usuario

Guía para clonar, instalar y correr el proyecto desde cero, pensada para
alguien que nunca ha visto el repositorio.

## Qué hace esto

Toma los archivos crudos de los cuatro operadores de transporte
(Transmetro, Transurbano, MetroRiel, Aerómetro), que no comparten
formato, moneda, llave de usuario ni nombre de zona, y los integra en un
solo modelo de datos consultable con SQL, en tres capas: Bronze, Silver y
Gold.

## Antes de empezar

Hace falta tener instalado Python 3.11 o superior y Git. Se puede
verificar con `python --version` y `git --version`. No hace falta Docker,
Postgres ni Tableau para esta fase, todo corre con Python y DuckDB, que
es una base de datos que vive en un solo archivo sin servidor que
instalar.

## Clonar el repositorio

```bash
git clone https://github.com/danielpazortega16/pryecto-ciencia-de-datos.git
cd pryecto-ciencia-de-datos
```

## Instalar las dependencias

```bash
pip install duckdb dbt-duckdb prefect
```

duckdb es el motor de base de datos donde queda staging, silver y gold.
dbt-duckdb es la herramienta que corre las transformaciones en SQL.
prefect es el orquestador que encadena todo el flujo.

## Generar los datos

Los archivos crudos no están en el repositorio porque pesan alrededor de
130 MB, se generan localmente:

```bash
python generar_red_metropolitana.py
```

Esto crea la carpeta datos_red con los 9 archivos: catálogos y operación
de los cuatro operadores más el CDC del padrón. Tarda unos segundos.

## Correr el pipeline completo

Un solo comando hace la ingesta a Bronze, las transformaciones de
staging a silver a gold, y las pruebas de calidad:

```bash
python orquestacion/flow_prefect.py
```

En pantalla primero aparece una tabla de conteos por archivo de la
ingesta, después la lista de modelos de dbt terminando cada uno en OK, y
al final las 13 pruebas de dbt test en PASS. Si todo terminó así, el
pipeline corrió bien.

Este comando se puede correr las veces que se quiera el mismo día sin
duplicar nada, porque Bronze sobreescribe la carga del día y Silver y
Gold se recalculan completos cada vez.

## Revisar los resultados

Los datos finales quedan en un archivo warehouse.duckdb en la raíz del
proyecto. Se puede consultar así:

```python
import duckdb
con = duckdb.connect("warehouse.duckdb", read_only=True)

con.execute("""
    select operador, count(*) as abordajes
    from main_gold.fact_abordaje
    group by 1 order by 2 desc
""").fetchall()

con.execute("select * from main_staging.stg_padron_transmetro_vigente limit 5").fetchall()

con.execute("select * from main_silver.silver_cuarentena limit 5").fetchall()
```

También se puede abrir warehouse.duckdb con cualquier cliente de DuckDB,
por ejemplo la extensión de VS Code, o el CLI `duckdb warehouse.duckdb`.

## Problemas comunes

Si dbt no se reconoce como comando, probablemente no está en el PATH; se
puede confirmar que está instalado con `python -m pip show dbt-duckdb` y
llamarlo desde la carpeta Scripts de la instalación de Python.

Si aparece un error de que no se encuentran archivos que coincidan con el
patrón de bronze, es porque no se corrió primero la ingesta o porque la
variable PROJECT_ROOT no está seteada al llamar dbt manualmente; corriendo
`python orquestacion/flow_prefect.py` esto se configura solo.

Si faltan archivos en datos_red, hace falta correr primero
`python generar_red_metropolitana.py`.

Los conteos no deberían cambiar entre corridas, si cambian probablemente
se editó algo en datos_red a mano entre una corrida y otra.

## Dónde está cada cosa

generar_red_metropolitana.py genera los 9 archivos de datos crudos.
datos_red guarda esos datos (no se sube a git). src/ingesta tiene los
scripts que cargan datos_red hacia bronze. bronze guarda los datos crudos
en Parquet (tampoco se sube a git). dbt_project/models/staging hace la
limpieza mínima y el tipado de cada fuente. dbt_project/models/silver
unifica formatos, aplica cuarentena y el SCD2 del padrón.
dbt_project/models/gold tiene el modelo dimensional. warehouse.duckdb es
la base de datos final (no se sube a git). orquestacion/flow_prefect.py
corre todo el flujo con un solo comando. docs tiene toda la
documentación.

## Para entender las decisiones

Este manual explica cómo correrlo. Para entender por qué se construyó
así, el grano de la tabla de hechos, cómo se resolvió la identidad del
usuario, qué se manda a cuarentena y por qué, está docs/decisiones.md.
La matriz del bus está en docs/matriz_bus.md y todas las cifras medidas
en docs/metricas.md.
