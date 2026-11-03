# Bitácora del Proyecto 2

Cada corrida que se reporta en los informes se puede repetir con el
comando indicado. Semilla 42 en todo el proyecto.

## 2026-11-03 - Carga de los datos nuevos desde cero

`python orquestacion/flow_prefect.py --desde-cero`. Se vaciaron bronze/,
warehouse.duckdb y dbt_project/target antes de cargar. Los 9 archivos
llegaron a Bronze con exactamente las filas que publica el LEEME
(docs/proyecto2/conteos_carga.csv). 67 segundos en total
(docs/proyecto2/tiempos_carga.csv). Se agregó a Silver el modelo
silver_cdc_padron (todo el CDC, con la llave numérica de la persona) para
poder aplicar la regla de bajas de la población.

## 2026-11-03 - Población, etiqueta y features de los cortes A, B y C

`python -m ml.construir_dataset` (corre dentro del flujo). Corte A: 7,095 /
59,491 = 0.1193. Corte B: 6,387 / 58,113 = 0.1099. Corte C: 57,701
unidades, etiqueta oculta.

## 2026-11-03 - Prueba de recorte

`python -m ml.prueba_recorte --nivel silver` y `--nivel crudo`. 59,491
filas comparadas en los dos niveles, 0 diferencias. Ninguna feature falló.
En el nivel crudo se recortaron los 9 archivos al 30 de junio y se corrió el
pipeline completo en una copia aislada del proyecto.

## 2026-11-03 - Feature retirada

n_tarjetas daba exactamente lo mismo que n_operadores (cada persona tiene
una sola tarjeta por operador) y la logística le repartía el mismo
coeficiente a las dos. Se quitó y se volvió a correr todo lo anterior. No
es una fuga, es una columna redundante.

## 2026-11-03 - Ensembles y modelo para produccion

`python -m ml.fase2_ensemble`. Mismos 5 folds del corte A. PR-AUC en
validacion: logistica L2 0.415, HistGradientBoosting 0.426, Random Forest
0.424. El boosting gana a la logistica en los 5 folds (de +0.007 a +0.016).
Se elige HistGradientBoosting para produccion.

## 2026-11-03 - Umbral

`python -m ml.umbral --modelo "HistGradientBoosting"` sobre las predicciones
fuera de fold del corte A. Umbral 0.325 (el teorico es 1/3). Ganancia en A:
Q11,480 contactando a 6,320 personas.

## 2026-11-03 01:44:39 - Evaluacion unica en el corte B

Commit 3a6bb7c0c33a3bc1349b2978e7dab77022a1f5ee. Modelo hgb entrenado con todo el corte A, umbral 0.325. PR-AUC en B 0.3862 (baseline tasa 0.1099, baseline dias sin viajar 0.3593). Ganancia Q7,550. No se ajusto nada despues de ver este resultado.
