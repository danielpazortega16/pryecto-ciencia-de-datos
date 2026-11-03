# Proyecto 2 - Fase 1

## Introducción

En este proyecto queremos estimar qué personas van a dejar de usar la red
de transporte en los próximos 30 días, para que la Agencia pueda decidir a
quién contactar en una campaña de retención. Usamos el mismo pipeline del
Proyecto 1 para cargar los datos y sobre eso armamos la etiqueta, las
features y los primeros modelos.

Los datos son simulados y no corresponden a ningún operador ni usuario
real.

## Datos nuevos desde cero

Para cargar todo desde un entorno vacío se corre un solo comando:

```
python orquestacion/flow_prefect.py --desde-cero
```

Este comando borra el lake, el warehouse y lo que dbt genera, carga los
nueve archivos de la carpeta datos_red, corre staging, silver y gold con
sus pruebas y al final calcula las features de los tres cortes. No hay
pasos manuales. dbt crea sus vistas de Bronze al arrancar y no usamos
seeds ni tablas incrementales, así que Silver y Gold se recalculan
completos cada vez.

| Archivo | Filas esperadas | Filas en Bronze | Diferencia |
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

Los nueve archivos llegaron completos a Bronze, así que no hubo
diferencias que explicar. La limpieza de duplicados, nulos, fechas futuras
y viajes sin salida pasa después, en Silver, y lo que se rechaza queda en
cuarentena.

Estos son los tiempos de una corrida desde cero en nuestra máquina:

| Etapa | Segundos |
|---|---:|
| Vaciar lake y warehouse | 0.2 |
| Ingesta a Bronze | 1.8 |
| dbt run | 38.1 |
| dbt test | 16.4 |
| Exportar los CSV del tablero | 0.3 |
| Features de los cortes A, B y C | 10.3 |
| Total | 67.1 |

## Etiqueta, población y unidad

### Etiqueta

Una persona tiene etiqueta 1 si no tiene ningún abordaje válido
en ningún operador desde las 00:00 del día de corte hasta 30 días después.
Si tiene al menos uno, su etiqueta es 0.

### Unidad

En el Proyecto 1 dejamos dos niveles de identidad: la tarjeta de
cada operador y la persona, con el supuesto de que el número dentro de la
tarjeta es el mismo para Transmetro, Transurbano y MetroRiel. Por ejemplo
TC-00013132, 0000013132 y MR0013132 serían la misma persona. Si usáramos la
tarjeta como unidad, alguien que deja Transmetro pero sigue viajando en
Transurbano contaría como abandono, y a esa persona no hace falta
contactarla. Por eso trabajamos con la persona. Aerómetro entrega un hash
que no se puede enlazar con nada, así que cada tarjeta de Aerómetro cuenta
como una persona aparte.

### Población

Entra a un corte la persona que tiene al menos 2 abordajes
válidos en los 28 días anteriores y que no tiene un DELETE vigente en el
padrón antes del corte.

| Corte | Fecha | Población | Positivos | Tasa |
|---|---|---:|---:|---:|
| A | 1 de julio de 2026 | 59,491 | 7,095 | 0.1193 |
| B | 31 de julio de 2026 | 58,113 | 6,387 | 0.1099 |
| C | 30 de agosto de 2026 | 57,701 | oculta | oculta |

La tasa sale de dividir los positivos entre la población, por ejemplo
7,095 entre 59,491 da 0.1193 en el corte A.

### Costo de la unidad

Lo medimos de dos formas. Primero armamos la misma
población y etiqueta pero con la tarjeta como unidad. En el corte A hay
10,812 tarjetas positivas y en 2,404 de ellas la persona siguió viajando
con otra tarjeta, o sea 0.222 de los positivos. En el corte B fueron 2,400
de 10,004, que es 0.240. Con la tarjeta, más o menos uno de cada cinco
abandonos sería falso.

Lo segundo es lo que nos cuesta usar la persona. Las tarjetas de Aerómetro
no se pueden enlazar, así que en el corte A son 10,429 de las 59,491
personas, y 1,460 de los 7,095 positivos son solo de Aerómetro, que es
0.206. Si alguna de esas personas siguió viajando con otra tarjeta, es un
abandono falso que no podemos medir. En el corte B fueron 1,360 de 6,387,
que es 0.213.

## Features a la fecha de corte y auditoría de fuga

El código recibe la fecha de corte como parámetro y calcula los tres cortes
con la misma función. Los resultados se apilan en una sola tabla con la
fecha de corte como columna, con 175,305 filas en total: 59,491 de A,
58,113 de B y 57,701 de C. La tabla queda en el warehouse y también en un
archivo parquet.

Calculamos 19 features con ventanas de 28 días o menos, iguales en los tres
cortes. Miden cuántos días lleva la persona sin viajar, cuántos viajes hizo
en 7, 14 y 28 días, si viene bajando, cuántos días estuvo activa, qué
operadores usa, a qué horas viaja, cuánto gastó y su perfil en el padrón.
Todas salen de Silver, así que lo que está en cuarentena no entra. La lista
completa está en el diccionario de features del repositorio.

Para revisar que no hubiera fuga hicimos la prueba de recorte. Calculamos
las features del corte A con los datos completos y otra vez con los datos
cortados al 30 de junio, y comparamos las dos tablas. La hicimos en dos
niveles:

| Nivel | Qué se recorta | Filas | Diferencias |
|---|---|---:|---:|
| Silver | Los eventos de Silver y del padrón antes del 1 de julio | 59,491 | 0 |
| Crudo | Los 9 archivos originales, corriendo todo el pipeline en una copia aparte | 59,491 | 0 |

Ninguna feature tuvo diferencias, así que no hubo que corregir ninguna. El
nivel crudo es el más exigente porque también detectaría una fuga dentro
del pipeline, por ejemplo una deduplicación que mire datos futuros. En ese
nivel un viaje de MetroRiel solo se queda si ya había terminado antes del
corte, porque el operador entrega el viaje hasta que se cierra. La prueba se
repite con estos comandos:

```
python -m ml.prueba_recorte --nivel silver
python -m ml.prueba_recorte --nivel crudo
```

## Línea base y regresión logística regularizada

Como métrica usamos la PR-AUC. Solo el 11.9% de la población del corte A
abandona y la Agencia no va a contactar a todos, sino que va a ordenar a
las personas por riesgo y empezar por las de arriba. La PR-AUC mide qué tan
arriba de esa lista quedan los que se van, y a diferencia de la ROC-AUC no
se infla con los miles de negativos fáciles. Además su línea base es fácil
de leer: un modelo que no sabe nada saca la tasa de positivos, 0.119. La
ROC-AUC la reportamos al lado solo como referencia.

Todos los modelos usan los mismos 5 folds estratificados del corte A con
semilla 42. La etiqueta del corte B no se usó en esta fase. El escalado y el
one-hot del perfil van dentro de un Pipeline, así que se ajustan solo con
el fold de entrenamiento.

| Modelo | PR-AUC validación | Desviación | ROC-AUC |
|---|---:|---:|---:|
| Línea base 1: a todos la tasa del corte A | 0.119 | 0.000 | 0.500 |
| Línea base 2: días desde el último viaje | 0.403 | 0.014 | 0.826 |
| Línea base 3: menos viajes en 28 días | 0.254 | 0.004 | 0.743 |
| Logística L2, λ = 100 | 0.415 | 0.016 | 0.831 |
| Logística L1, λ = 10 | 0.414 | 0.016 | 0.831 |
| Logística Elastic Net, λ = 10 | 0.415 | 0.016 | 0.831 |

La línea base 2 no entrena nada, solo ordena a las personas por los días
que llevan sin viajar. La elegimos porque dejar de viajar es justo como
empieza el abandono. Resultó ser muy fuerte, ya que la logística solo le
gana por 0.012, menos que la desviación entre folds. Eso nos dice que casi
toda la señal está en la recencia y que lo demás aporta poco.

Para la regularización probamos λ desde 0.001 hasta 1,000 con los tres
castigos y elegimos el que dio mayor PR-AUC media en validación: L2 con
λ = 100, y L1 y Elastic Net con λ = 10. En scikit-learn 1.8 el tipo de
castigo se elige con l1_ratio y la fuerza con C, que es 1 entre λ. Con unas
47,000 filas por fold y 19 features, el resultado casi no cambia hasta
λ = 10. De ahí para arriba L1 y Elastic Net empiezan a perder porque
mandan a cero coeficientes que sí servían. Los tres castigos quedaron
prácticamente empatados.

![PR-AUC contra lambda](logistica_pr_auc_vs_lambda.png)

Estos son los coeficientes que más empujan hacia el abandono, de la
logística L2 con λ = 100 entrenada con todo el corte A y con las variables
escaladas:

| Feature | Coeficiente | Cómo se lee |
|---|---:|---|
| Días desde el último viaje | +0.764 | Cada día de más sin viajar sube el riesgo. Es la señal más fuerte. |
| Viajes en 28 días | +0.332 | Si los viajes de la última semana y los días activos se quedan iguales, tener más viajes en el mes quiere decir que antes viajaba más y ya no. |
| Perfil general | +0.227 | En el corte A abandona el 17.5% de este perfil, contra 11.9% de toda la población. |
| Perfil estudiante | +0.100 | También abandonan más que el promedio, el 15.9%. |
| Viajes en 14 días | +0.086 | Igual que el anterior, viajes concentrados en la semana pasada y no en esta indican que se está yendo. |

Del otro lado, lo que más protege es tener muchos días activos, con −0.633,
haber viajado en la última semana, con −0.519, y no estar en el padrón, con
−0.312. En el corte A abandona el 11.3% de quienes no están en el padrón,
contra entre 12.2% y 17.5% de los que sí tienen un perfil registrado.
