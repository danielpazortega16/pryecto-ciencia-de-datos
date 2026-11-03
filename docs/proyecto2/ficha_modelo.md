# Ficha del modelo: abandono de la red, v1

**Aviso: los datos son simulados.** No corresponden a ningún operador ni
usuario real; las cifras sirven para el curso, no para decisiones reales.

**Qué hace.** Estima la probabilidad de que una persona no tenga ningún
abordaje válido en los 30 días que empiezan en la fecha de corte, y marca a
quién conviene contactar en una campaña de retención.

**Datos y periodo.** Los nueve archivos de la Red Metropolitana, versión 2,
del 1 de junio al 29 de agosto de 2026, cargados con el pipeline del
Proyecto 1 hasta la capa Silver (solo registros válidos; lo que está en
cuarentena no entra).

**Unidad.** La persona: el número dentro de la tarjeta vincula Transmetro,
Transurbano y MetroRiel. Cada tarjeta de Aerómetro cuenta como persona
aparte, porque su llave es un hash que no se puede enlazar.

**Población.** Personas con al menos 2 abordajes válidos en los 28 días
anteriores al corte y sin un DELETE vigente en el CDC antes del corte.

**Etiqueta.** 1 si no hay ningún abordaje válido, en ningún operador, entre
el corte y 30 días después; 0 si hay al menos uno.

**Features.** 19 variables con una ventana de 28 días antes del corte
(recencia, frecuencia, tendencia, mezcla de operadores, horario, gasto y
perfil del padrón). Diccionario en diccionario_features.md.

**Modelo.** HistGradientBoostingClassifier dentro de un Pipeline de
scikit-learn 1.8.0, entrenado con todo el corte A (1 de julio). Archivo:
modelos/modelo_abandono_v1.joblib. Semilla 42.

**Métricas.**

| | PR-AUC | ROC-AUC | Línea base (recencia) | Línea base (tasa) |
|---|---:|---:|---:|---:|
| Validación cruzada, corte A (5 folds) | 0.426 ± 0.015 | 0.841 | 0.403 | 0.119 |
| Test único, corte B | 0.386 | 0.839 | 0.359 | 0.110 |

**Umbral y su costo.** Se contacta si el puntaje es ≥ 0.325. Escenario:
contactar cuesta Q5, la campaña retiene al 25% de quienes se iban a ir y
cada retenido vale Q60, así que G = 10 × VP − 5 × FP. El umbral maximiza G
en el corte A (Q11,480, precisión 0.454, recall 0.405). En el corte B dejó
Q7,550 (precisión 0.408, recall 0.430). Contactar a todos perdería
Q191,030 en el corte A.

**Fugas revisadas.** Las features solo usan eventos anteriores a las 00:00
del corte y la etiqueta solo los 30 días siguientes. Prueba de recorte del
corte A: 0 diferencias recortando Silver y recortando los archivos crudos.
Prueba de invariancia ensayada con el corte B: predicciones idénticas con y
sin los 30 días posteriores. El corte B se usó una sola vez.

**Limitaciones.**

- El vínculo entre tarjetas es un supuesto. Si dos números iguales fueran
  personas distintas, se mezclarían; si una persona usa Aerómetro y otro
  operador, se cuenta dos veces. 1,460 de los 7,095 positivos del corte A
  (0.206) son solo de Aerómetro y no se pueden verificar.
- Casi toda la señal está en la recencia: el modelo le gana al baseline de
  días sin viajar por 0.023 de PR-AUC en validación y 0.027 en B.
- La ganancia depende de cuánta gente abandona: en B, con menos abandono, la
  misma campaña rinde menos.
- Entrenado con un solo mes (junio) para predecir julio: no vio
  estacionalidad, vacaciones ni cambios de tarifa.
- El efecto de la campaña (25% de retención) es un supuesto del escenario,
  no algo medido.

**Uso.** `python predecir.py --datos datos_red --fecha-corte 2026-08-30`.
Equipo: Daniel Paz (1200022) y Jonathan García (1045222). Versión v1, 3 de
noviembre de 2026.
