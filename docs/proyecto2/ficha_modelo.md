# Ficha del modelo de abandono, versión 1

Los datos son simulados y no corresponden a ningún operador ni usuario
real. Las cifras sirven para el curso y no para tomar decisiones reales.

### Qué hace

Estima la probabilidad de que una persona no tenga ningún abordaje válido
en los 30 días que empiezan en la fecha de corte, y marca a quién conviene
contactar en una campaña de retención.

### Datos

Los nueve archivos de la Red Metropolitana, del 1 de junio al 29 de agosto
de 2026, cargados con el pipeline del Proyecto 1 hasta Silver. Solo se usan
registros válidos, lo que está en cuarentena no entra.

### Unidad, población y etiqueta

La unidad es la persona. El número dentro de la tarjeta une Transmetro,
Transurbano y MetroRiel, y cada tarjeta de Aerómetro cuenta aparte porque
no se puede enlazar. Entran las personas con al menos 2 abordajes en los 28
días antes del corte y sin un DELETE vigente en el padrón. La etiqueta es 1
si no viajan en ningún operador en los 30 días desde el corte.

### Features y modelo

Son 19 variables de los 28 días antes del corte: recencia, frecuencia,
tendencia, operadores, horario, gasto y perfil. El modelo es un
HistGradientBoostingClassifier dentro de un Pipeline de scikit-learn 1.8.0,
entrenado con todo el corte A del 1 de julio y con semilla 42. Está
guardado en modelos/modelo_abandono_v1.joblib.

### Métricas

| | PR-AUC | ROC-AUC | Línea base de recencia | Línea base de la tasa |
|---|---:|---:|---:|---:|
| Validación cruzada en el corte A | 0.426 ± 0.015 | 0.841 | 0.403 | 0.119 |
| Test único en el corte B | 0.386 | 0.839 | 0.359 | 0.110 |

### Umbral

Se contacta a quien tenga un puntaje de 0.325 o más. Contactar cuesta Q5,
la campaña retiene al 25% de quienes se iban a ir y cada retenido vale Q60,
entonces la ganancia es G = 10 × VP - 5 × FP. En el corte A el umbral dejó Q11,480 con precisión de
0.454 y recall de 0.405. En el corte B dejó Q7,550 con precisión de 0.408 y
recall de 0.430. Contactar a todos perdería Q191,030 en el corte A.

### Revisión de fugas

Las features solo usan lo que pasó antes de las 00:00 del corte y la
etiqueta solo los 30 días siguientes. La prueba de recorte del corte A no
dio diferencias ni en Silver ni en los archivos crudos. El ensayo de
invariancia con el corte B dio predicciones idénticas con y sin los 30 días
siguientes. El corte B se evaluó una sola vez.

### Limitaciones

- El enlace entre tarjetas es un supuesto. 1,460 de los 7,095 positivos del corte A son solo de Aerómetro y no se pueden verificar.
- Casi toda la señal está en la recencia. El modelo le gana a la línea base de días sin viajar por 0.023 en validación y por 0.027 en B.
- Si abandona menos gente, como pasó en B, la misma campaña deja menos ganancia.
- Se entrenó con un solo mes, así que no vio vacaciones, temporadas ni cambios de tarifa.
- El 25% de retención es un supuesto del escenario y no algo que se haya medido.

### Uso

```
python predecir.py --datos datos_red --fecha-corte 2026-08-30
```

Daniel Paz, 1200022, y Jonathan García, 1045222. Versión 1, 3 de noviembre
de 2026.
