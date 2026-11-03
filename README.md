# Agencia Metropolitana de Transporte

Repositorio de los dos proyectos de Ciencia de Datos. En el Proyecto 1
armamos la plataforma de datos de la red de transporte. En el Proyecto 2
hicimos un modelo que estima qué personas van a dejar de usar la red en
los próximos 30 días y a quiénes conviene contactar. La versión final del
Proyecto 1 quedó en la etiqueta proyecto-1.

## Proyecto 2

Se necesita Python 3.13 y las librerías de requirements.txt, que tienen
las versiones fijas:

```bash
pip install -r requirements.txt
```

Para cargar todo desde cero se corre este comando. Borra el lake, el
warehouse y lo que genera dbt, vuelve a cargar la carpeta datos_red y
calcula las features de los cortes A, B y C:

```bash
python orquestacion/flow_prefect.py --desde-cero
```

Para sacar las predicciones de una fecha de corte con el modelo guardado,
sin volver a entrenar:

```bash
python predecir.py --datos datos_red --fecha-corte 2026-08-30
```

Estos son los demás pasos en el orden en que los corrimos. Cada uno guarda
sus resultados en docs/proyecto2:

```bash
python -m ml.prueba_recorte --nivel silver
python -m ml.prueba_recorte --nivel crudo
python -m ml.costo_unidad
python -m ml.fase1_modelos
python -m ml.fase2_ensemble
python -m ml.umbral --modelo "HistGradientBoosting"
python -m ml.evaluar_test_b --modelo hgb
python -m ml.segmentos --k 5
python -m ml.prueba_invariancia
```

La evaluación en el corte B solo se puede correr una vez. Si ya existe el
resultado, el script no la vuelve a hacer. La prueba de invariancia ensaya
con el corte B lo mismo que se hace en la defensa y al terminar deja otra
vez las predicciones del corte C.

Para revisar que las predicciones del corte C no cambian con datos nuevos,
se corre predecir.py con la carpeta que trae los 30 días más y se compara
con el archivo que ya estaba:

```bash
python predecir.py --datos ruta/datos_nuevos --fecha-corte 2026-08-30 --salida predicciones/pred_nuevos.csv
fc predicciones\predicciones_2026-08-30.csv predicciones\pred_nuevos.csv
```

Los informes, la ficha del modelo y la presentación están en
docs/proyecto2, junto con la bitácora de corridas. La semilla es 42 en todo
el proyecto.

## Proyecto 1

Pipeline Bronze, Silver y Gold para juntar los datos de los cuatro
operadores de la ciudad: Transmetro, Transurbano, MetroRiel y Aerómetro.
Cada uno entrega sus datos con otro formato, otra llave de usuario, otra
moneda y otra forma de definir las zonas. Las razones de cada decisión
están en docs/decisiones.md.

### Requisitos

Python 3.11 o más reciente con duckdb, dbt-duckdb y prefect. No hace falta
Docker ni Postgres. En docs/decisiones.md explicamos por qué no usamos
Kafka.

```bash
pip install duckdb dbt-duckdb prefect
```

### Estructura

- generar_red_metropolitana.py: el generador de datos del curso.
- datos_red: los 9 archivos generados. No se sube a git.
- src/ingesta: los scripts que cargan Bronze.
- bronze: el lake en Parquet, separado por fecha de carga. No se sube a git.
- dbt_project: los modelos de staging, silver y gold.
- warehouse.duckdb: la base con staging, silver y gold. No se sube a git.
- orquestacion/flow_prefect.py: corre todo el flujo con Prefect.
- tableau: el tablero y los CSV que usa.
- docs: decisiones, métricas, DDL, matriz del bus y manual de usuario.

### Cómo correr el flujo completo

Primero se generan los datos si todavía no existen:

```bash
python generar_red_metropolitana.py
```

Luego un solo comando corre la ingesta, las transformaciones y las
pruebas de calidad:

```bash
python orquestacion/flow_prefect.py
```

Se puede correr varias veces el mismo día sin duplicar nada. Bronze
reemplaza la carga del día y Silver y Gold se recalculan completos cada
vez. En docs/evidencia_idempotencia.json están los conteos de dos corridas
seguidas.

Para correr solo la ingesta:

```bash
python src/ingesta/run_ingesta_bronze.py
```

Para correr solo dbt hay que definir antes la variable PROJECT_ROOT con la
ruta del proyecto, usando / aunque sea Windows, porque dbt la usa para
encontrar bronze y el warehouse. Después, desde la carpeta dbt_project:

```bash
dbt run --profiles-dir .
```

### Consultar el resultado

```python
import duckdb
con = duckdb.connect("warehouse.duckdb", read_only=True)
con.execute("select * from main_gold.fact_abordaje limit 10").fetchall()
```

### Documentación

En docs/MANUAL_USUARIO.md está la guía paso a paso para alguien que nunca
ha visto el repositorio. Las decisiones de grano, identidad del usuario,
zonas, cuarentena e idempotencia están en docs/decisiones.md, y las cifras
medidas en docs/metricas.md.

La arquitectura y el modelo están en docs/diagrama_modelo.md,
docs/matriz_bus.md, docs/ddl_gold.sql y docs/linaje.md, que sigue cada
tabla de gold hasta su archivo original.

La gobernanza y la seguridad están en docs/diccionario_datos.md,
docs/definiciones_oficiales.md y docs/seguridad.md.

La recomendación para la Agencia está en docs/recomendacion.md, las
features en docs/features.md y el tablero en docs/tablero.md.

### Variables de entorno

PSEUDO_SALT es la sal con la que se seudonimiza la tarjeta. Si no está
definida se usa una de desarrollo. Para una corrida real hay que definirla
como en .env.example. No se sube al repositorio.

### Verificar idempotencia

```bash
python src/ingesta/verificar_idempotencia.py
```

Corre la ingesta y dbt dos veces y compara los conteos de silver, gold y
features. Al final debe decir que los conteos son idénticos.

### Tablero

El tablero está en tableau/tablero_agencia.twbx y se explica en
docs/tablero.md. Se abre con Tableau Public o Tableau Desktop.
