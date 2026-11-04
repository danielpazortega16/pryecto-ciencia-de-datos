# Proyecto 2 - Fase 1

## Introducción

Cada mes una parte de los usuarios deja de viajar en la red y la mayoría no
avisa. La Agencia quiere hacer una campaña de retención, pero el presupuesto
no alcanza para todos, entonces necesita saber a quién contactar. En esta
fase cargamos los datos nuevos con el pipeline del Proyecto 1, definimos la
etiqueta, armamos las features y probamos los primeros modelos.

Los datos son simulados y no corresponden a ningún operador ni usuario real.

## 1.1 Datos nuevos desde cero

Para cargar todo desde un entorno vacío corrimos este comando, que también
está en el README:

```
python orquestacion/flow_prefect.py --desde-cero
```

Primero borra el lake, el warehouse y lo que genera dbt. Después carga los
nueve archivos de datos_red, corre staging, silver y gold con sus pruebas y
calcula las features de los tres cortes. No hay que hacer nada a mano, porque
dbt crea sus vistas de Bronze al arrancar y no usamos seeds, snapshots ni
tablas incrementales.

| Archivo | Filas esperadas | Filas cargadas | Diferencia |
|---|---:|---:|---:|
| aerometro_boardings.csv | 387,053 | 387,053 | 0 |
| am_estaciones.csv | 14 | 14 | 0 |
| cdc_padron_usuarios.csv | 77,636 | 77,636 | 0 |
| metroriel_viajes.jsonl | 590,844 | 590,844 | 0 |
| mr_estaciones.csv | 22 | 22 | 0 |
| tm_estaciones.csv | 104 | 104 | 0 |
| transmetro_validaciones.csv | 713,786 | 713,786 | 0 |
| transurbano_transacciones.csv | 1,635,788 | 1,635,788 | 0 |
| tu_paradas.csv | 328 | 328 | 0 |

Los nueve archivos cuadraron con la tabla de conteos esperados. Los
duplicados, nulos, fechas futuras y viajes sin salida se limpian después en
Silver, y lo que se rechaza queda en cuarentena.

Estos fueron los tiempos de la primera corrida:

| Etapa | Segundos |
|---|---:|
| Vaciar lake y warehouse | 0.2 |
| Ingesta a Bronze | 1.8 |
| dbt run | 38.1 |
| dbt test | 16.4 |
| Exportar los CSV del tablero | 0.3 |
| Features de los cortes A, B y C | 10.3 |
| Total | 67.1 |

En una corrida posterior el total bajó a 24.6 segundos. El archivo
docs/proyecto2/tiempos_carga.csv guarda siempre la última corrida.

## 1.2 Etiqueta, población y unidad

### Etiqueta

Una unidad tiene etiqueta 1 si no tiene ningún abordaje válido, en ningún
operador, en los 30 días que empiezan a las 00:00 del corte, y 0 si tiene al
menos uno.

### Unidad

Elegimos la persona. En el Proyecto 1 dejamos dos niveles de identidad, la
tarjeta de cada operador y la persona, con el supuesto de que TC-00013132,
0000013132 y MR0013132 son la misma porque tienen el mismo número. Si
usáramos la tarjeta, alguien que deja Transmetro pero sigue en Transurbano
contaría como abandono y la Agencia gastaría en contactarlo. Aerómetro
entrega un hash que no se puede enlazar, por eso cada tarjeta suya cuenta
como una persona aparte.

### Población

Entra a un corte la persona que tiene al menos 2 abordajes válidos en los 28
días anteriores y sin un DELETE del CDC aplicado antes del corte. La llave
del CDC se enlaza con la persona por el mismo número.

| Corte | Fecha | Población | Positivos | Tasa positiva | Cuenta |
|---|---|---:|---:|---:|---|
| A | 1 de julio | 59,491 | 7,095 | 0.1193 | 7,095 / 59,491 = 0.1193 |
| B | 31 de julio | 58,113 | 6,387 | 0.1099 | 6,387 / 58,113 = 0.1099 |
| C | 30 de agosto | 57,701 | oculta | oculta | no se puede calcular |

### Costo de la unidad

Lo medimos por los dos lados. Para ver lo que nos ahorramos con la persona,
armamos la misma población y etiqueta con la tarjeta como unidad y contamos
las tarjetas positivas cuya persona siguió viajando con otra tarjeta:

- Corte A: 2,404 de 10,812 positivos = 0.222
- Corte B: 2,400 de 10,004 positivos = 0.240

Con la tarjeta, más o menos uno de cada cinco abandonos habría sido falso.

Lo que nos cuesta la persona es Aerómetro. En el corte A son 10,429 de las
59,491 unidades. Si alguien de ahí siguió viajando con una tarjeta de otro
operador, cuenta como abandono y no lo podemos saber. Contamos los positivos
que solo tienen tarjeta de Aerómetro:

- Corte A: 1,460 de 7,095 positivos = 0.206
- Corte B: 1,360 de 6,387 positivos = 0.213

## 1.3 Features a la fecha de corte y auditoría de fuga

La función construir de ml/features.py recibe la fecha de corte como
parámetro y calcula los tres cortes con el mismo código. Todo queda en una
sola tabla, con una fila por unidad en cada corte: 175,305 filas, de las que
59,491 son de A, 58,113 de B y 57,701 de C. Tiene las columnas unidad_id,
corte, fecha_corte, tarjetas, las 19 features y etiqueta, que queda vacía en
C. Está en el warehouse como main_ml.features y también en
ml/salidas/features_cortes.parquet.

Las features miden los días sin viajar, los viajes en 7, 14 y 28 días, si la
persona viene bajando, los días activos, los operadores que usa, las horas a
las que viaja, cuánto gastó y su perfil en el padrón. Ninguna ventana pasa de
28 días y son iguales en los tres cortes. Todo sale de Silver, entonces lo que
está en cuarentena no entra. El diccionario, con nombre, qué mide, ventana y
tabla de origen de cada una, está en docs/proyecto2/diccionario_features.md.

Para la auditoría de fuga calculamos las features del corte A con los datos
completos y otra vez con los datos recortados al 30 de junio, en dos niveles:

| Nivel | Qué se recorta | Filas comparadas | Diferencias |
|---|---|---:|---:|
| Silver | Eventos de Silver y del CDC anteriores al 1 de julio | 59,491 | 0 |
| Crudo | Los 9 archivos originales, con todo el pipeline en una copia aparte | 59,491 | 0 |

Ninguna feature falló, por lo que la lista de features corregidas está
vacía. El nivel crudo es el más estricto porque también atraparía una fuga
del pipeline, como una deduplicación que mire datos futuros. Ahí un viaje de
MetroRiel solo se queda si ya había terminado antes del corte, porque el
operador lo entrega hasta que se cierra. Se repite con:

```
python -m ml.prueba_recorte --nivel silver
python -m ml.prueba_recorte --nivel crudo
```

## 1.4 Línea base y regresión logística regularizada

### Métrica

Elegimos la PR-AUC. Solo el 11.9% del corte A abandona y la Agencia no va a
contactar a todos, va a ordenar a las personas por riesgo y empezar por las
de arriba. La PR-AUC mide qué tan arriba quedan los que se van y no sube por
los miles de negativos fáciles, como le pasa a la ROC-AUC. Un modelo que no
sabe nada saca la tasa positiva, 0.119, y ese es el piso. La ROC-AUC la
ponemos al lado solo como referencia.

### Modelos

Todos usan los mismos 5 folds estratificados del corte A con semilla 42,
guardados en ml/salidas/folds_A.csv. No usamos la etiqueta del corte B en esta
fase. El escalado y el one-hot del perfil van dentro de un Pipeline, así se
ajustan solo con el fold de entrenamiento.

| Modelo | PR-AUC media | Desviación | ROC-AUC |
|---|---:|---:|---:|
| Línea base 1: a todos la tasa del corte A | 0.119 | 0.000 | 0.500 |
| Línea base 2: días desde el último viaje | 0.403 | 0.014 | 0.826 |
| Línea base 3: menos viajes en 28 días | 0.254 | 0.004 | 0.743 |
| Logística L2, λ = 100 | 0.415 | 0.016 | 0.831 |
| Logística L1, λ = 10 | 0.414 | 0.016 | 0.831 |
| Logística Elastic Net, λ = 10 | 0.415 | 0.016 | 0.831 |

La línea base 2 no entrena nada, solo ordena por los días que la persona lleva
sin viajar. La escogimos porque dejar de viajar es como empieza el abandono.
Salió bastante fuerte: la logística le gana por 0.012, menos que la desviación
entre folds. Casi toda la señal está en la recencia y lo demás aporta poco.

### Regularización

Probamos λ de 0.001 a 1,000 con los tres castigos y nos quedamos con el de
mayor PR-AUC media en validación: λ = 100 en L2 y λ = 10 en L1 y Elastic Net.
En scikit-learn 1.8 el castigo se elige con l1_ratio y la fuerza con C = 1 / λ.
Con unas 47,000 filas por fold y 19 features casi no cambia nada hasta λ = 10.
De ahí para arriba L1 y Elastic Net empiezan a perder porque mandan a cero
coeficientes que sí servían. Los tres castigos quedaron prácticamente
empatados.

![PR-AUC contra lambda](logistica_pr_auc_vs_lambda.png)

### Coeficientes

Estos son los 5 que más empujan hacia el abandono, de la logística L2 con
λ = 100 entrenada con todo el corte A y las variables escaladas:

| Feature | Coeficiente | Interpretación |
|---|---:|---|
| dias_desde_ultimo_viaje | +0.764 | Entre más días lleva sin viajar, más riesgo. Es la señal más fuerte y tiene sentido. |
| viajes_28d | +0.332 | Se lee junto con la última semana y los días activos, que restan. Con esos fijos, más viajes en el mes quiere decir que antes viajaba más y ya no. |
| perfil general | +0.227 | En el corte A abandona el 17.5% de este perfil, contra 11.9% del total. |
| perfil estudiante | +0.100 | También arriba del promedio, con 15.9%. |
| viajes_14d | +0.086 | Con la última semana fija, viajes concentrados en la semana anterior indican que se está yendo. |

Lo que más protege es tener muchos días activos, con -0.633, haber viajado en
la última semana, con -0.519, y no estar en el padrón, con -0.312. En el corte
A abandona el 11.3% de quienes no están en el padrón, contra entre 12.2% y
17.5% de quienes tienen un perfil registrado.
