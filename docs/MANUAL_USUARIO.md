# Manual de usuario — Pipeline Red Metropolitana

Guía paso a paso para clonar, instalar y correr el proyecto desde cero.
Pensada para alguien que nunca ha visto el repo (el profesor, un
compañero, o tú mismo en otra máquina).

---

## 1. Qué hace este proyecto

Toma los archivos crudos de los 4 operadores de transporte
(Transmetro, Transurbano, MetroRiel, Aerómetro), que no comparten
formato, moneda, llave de usuario ni nombre de zona, y los integra en un
único modelo de datos (Bronze → Silver → Gold) consultable con SQL.

---

## 2. Requisitos previos

Instalar antes de empezar:

| Herramienta | Para qué | Cómo verificar que ya la tienes |
|---|---|---|
| **Python 3.11 o superior** | Correr todo el pipeline | `python --version` |
| **Git** | Clonar el repositorio | `git --version` |
| **pip** (viene con Python) | Instalar librerías | `pip --version` |

No hace falta Docker, Postgres ni Tableau para esta fase — todo corre con
Python y DuckDB (una base de datos que vive en un solo archivo, sin
servidor que instalar).

---

## 3. Clonar el repositorio

```bash
git clone https://github.com/danielpazortega16/pryecto-ciencia-de-datos.git
cd pryecto-ciencia-de-datos
```

---

## 4. Instalar las dependencias de Python

```bash
pip install duckdb dbt-duckdb prefect
```

Esto instala:
- **duckdb**: el motor de base de datos que guarda Staging/Silver/Gold.
- **dbt-duckdb**: la herramienta que corre las transformaciones SQL.
- **prefect**: el orquestador que encadena todo el flujo.

---

## 5. Generar los datos de origen

Los archivos crudos (CSV/JSONL) no están en el repositorio porque pesan
~130 MB — se generan localmente con un script:

```bash
python generar_red_metropolitana.py
```

Esto crea la carpeta `datos_red/` con 9 archivos (catálogos + operación de
los 4 operadores + el CDC del padrón). Tarda unos segundos.

---

## 6. Correr el pipeline completo

Un solo comando hace todo: ingesta a Bronze → transformaciones (Staging →
Silver → Gold) → pruebas de calidad:

```bash
python orquestacion/flow_prefect.py
```

### Qué vas a ver en pantalla

1. **Ingesta a Bronze**: una tabla de conteos por archivo, por ejemplo:
   ```
   tm_validaciones     : 363221
   tu_transacciones    : 832791
   ...
   ```
2. **dbt run**: una lista de modelos (`stg_*`, `silver_*`, `dim_*`,
   `fact_*`) cada uno terminando en `OK`.
3. **dbt test**: 13 pruebas, todas en `PASS`.

Si todo terminó en verde, el pipeline corrió bien.

Este comando se puede correr **las veces que quieras** el mismo día sin
duplicar nada (es idempotente): Bronze sobreescribe la carga del día,
Silver y Gold se recalculan por completo cada vez.

---

## 7. Revisar los resultados

Los datos finales quedan en un archivo `warehouse.duckdb` en la raíz del
proyecto. Para consultarlo:

```bash
python
```
```python
import duckdb
con = duckdb.connect("warehouse.duckdb", read_only=True)

# Cuántos abordajes hay por operador
print(con.execute("""
    select operador, count(*) as abordajes
    from main_gold.fact_abordaje
    group by 1 order by 2 desc
""").fetchall())

# Ver el padron de Transmetro
print(con.execute("select * from main_staging.stg_padron_transmetro_vigente limit 5").fetchall())

# Ver por qué se rechazó un registro
print(con.execute("select * from main_silver.silver_cuarentena limit 5").fetchall())
```

También puedes abrir el archivo `warehouse.duckdb` con cualquier cliente
de DuckDB (por ejemplo la extensión de DuckDB en VS Code, o el CLI
`duckdb warehouse.duckdb`).

---

## 8. Solución de problemas comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `dbt: command not found` | El ejecutable de dbt no está en el PATH | Usa la ruta completa, ej. en Windows: `python -m pip show dbt-duckdb` para confirmar instalación, y llama a `dbt` desde la carpeta `Scripts` de tu Python |
| `No files found that match the pattern ...bronze/...` | No corriste primero la ingesta, o `PROJECT_ROOT` no está seteado | Corre `python orquestacion/flow_prefect.py` (ya lo configura solo) o exporta `PROJECT_ROOT` a la ruta absoluta del proyecto antes de llamar `dbt` manualmente |
| Faltan archivos en `datos_red/` | No corriste el generador | `python generar_red_metropolitana.py` (paso 5) |
| Los conteos cambian entre corridas | No debería pasar (el pipeline es idempotente) | Revisa que no hayas editado archivos en `datos_red/` a mano entre corridas |

---

## 9. Dónde está cada cosa

```
generar_red_metropolitana.py   # genera los 9 archivos de datos crudos
datos_red/                     # los datos generados (no se sube a git)
src/ingesta/                   # scripts que cargan datos_red/ -> bronze/
bronze/                        # datos crudos en Parquet (no se sube a git)
dbt_project/models/staging/    # limpieza mínima + tipado de cada fuente
dbt_project/models/silver/     # unificación de formatos, cuarentena, SCD2
dbt_project/models/gold/       # modelo dimensional (dim_*, fact_*)
warehouse.duckdb               # base de datos final (no se sube a git)
orquestacion/flow_prefect.py   # corre todo el flujo de un solo comando
docs/                          # toda la documentación del proyecto
```

## 10. Para entender las decisiones de diseño

Este manual explica **cómo correrlo**. Para entender **por qué** se
construyó así (grano de la tabla de hechos, cómo se resolvió la identidad
del usuario, qué se manda a cuarentena y por qué), lee:

- [`docs/decisiones.md`](decisiones.md) — el razonamiento detrás de cada
  decisión técnica.
- [`docs/matriz_bus.md`](matriz_bus.md) — qué dimensiones usa cada tabla
  de hechos.
- [`docs/metricas.md`](metricas.md) — todas las cifras medidas (volumen,
  calidad, CDC, rendimiento, idempotencia).
