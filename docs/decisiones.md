# Decisiones de diseño — Fase 1

## 1. Datos de origen

Se usó el `generar_red_metropolitana.py` oficial del curso (60,000 usuarios,
45 días, ESCALA=0.08, sembrado con `SEMILLA=2026`). Antes de recibirlo se
había construido un generador sustituto para no perder tiempo
(`docs/generador_sustituto_fase_inicial.py`, ya no se usa); se descartó en
cuanto llegó el oficial.

## 2. Ingesta y vía por fuente (1.1)

| Fuente | Vía | Por qué |
|---|---|---|
| Transmetro (validaciones) | Streaming (Kafka simulado) | Eventos de torniquete en producción llegan continuamente |
| Aerómetro (boardings) | Streaming (Kafka simulado) | Mismo argumento: evento por cabina |
| Transurbano (transacciones) | **Batch** (decisión libre) | El archivo trae fecha/hora en columnas separadas y el monto ya en centavos: forma típica de un extracto de liquidación consolidado al cierre, no un evento a capturar en el instante. Meter esto por streaming solo añade la complejidad de un tópico sin ganar nada — nadie en la Agencia necesita saber en tiempo real que alguien abordó un bus de Transurbano. Consecuencia: Transurbano siempre tendrá más latencia que Transmetro/Aerómetro; aceptable porque Fase 2 no pide demanda de Transurbano en tiempo real. |
| Los 4 catálogos + viajes MetroRiel | Batch | Catálogos cambian rara vez; MetroRiel entrega el viaje ya cerrado |
| Padrón de usuarios | CDC | Es el único archivo que se actualiza y se borra |

**Decisión de tiempo (Kafka):** por la ventana de entrega no se levantó
Kafka en Docker. `src/ingesta/ingesta_streaming.py` simula productor →
tópico → consumidor leyendo el CSV línea por línea y publicando cada fila
con una función `publicar_evento()` aislada del resto del pipeline,
precisamente para poder sustituirla por un productor/consumidor real de
Kafka sin tocar Bronze ni aguas abajo.

**Bronze: lake, no warehouse.** Vive en carpetas + Parquet particionadas
por `fecha_ingesta`, no en DuckDB. Motivo: uno de los archivos (MetroRiel)
es JSON anidado, y forzarlo a una tabla relacional en el aterrizaje solo
para deshacer esa estructura en Silver es trabajo de más. El warehouse
(DuckDB) arranca en Staging.

## 3. Staging y CDC (1.2)

El generador oficial mezcla formatos de llave en la columna `tarjeta` del
CDC a propósito (prioridad tm > tu > mr, o `SIN-TARJETA` si el usuario no
tiene ninguna). Esto es ambigüedad intencional del curso: el padrón que
pide 1.2 es "de Transmetro", pero el archivo trae de las cuatro.

**Decisión:** el padrón vigente de Transmetro se construye **solo** con
las filas del CDC cuya llave cumple el formato `TC-########`. El resto
(`stg_cdc_padron_raw.operador_detectado`) queda clasificado pero fuera del
padrón declarado — no se inventa un padrón "central" porque el enunciado
pide explícitamente el de Transmetro, y mezclar target ambiguo con
catálogos de otros operadores violaría la instrucción de no inventar datos
que el operador no entregó.

Conteo del CDC por operador detectado (ver `docs/metricas.md` para cifras
completas): la mayoría de filas sí son formato Transmetro; el resto
(`SIN-TARJETA`, formato TU, formato MR) se excluye del padrón de Transmetro
por diseño.

Los `DELETE` marcan la tarjeta como `INACTIVO`, nunca se borra la fila
(se conserva `perfil`/`zona_residencia` del último `INSERT`/`UPDATE`
conocido, porque el evento de borrado llega sin cuerpo).

Para Transurbano, MetroRiel y Aerómetro se construyó un catálogo mínimo
—solo la llave distinta que aparece en su propio archivo de operación—
sin inventar nombre, fecha de alta ni ningún otro atributo.

## 4. Capa Silver (1.3)

**Unificación de formatos:** fechas a timestamp único; Transurbano
(centavos → quetzales, `/100.0`); Aerómetro UTC → hora local restando 6
horas fijas (Guatemala no observa horario de verano).

**Zona conformada:** Transmetro, MetroRiel y Aerómetro ya entregan la zona
en forma canónica (`"Zona 10"`, `"Mixco"`, etc.) gracias a cómo el
generador arma sus catálogos. Solo Transurbano necesita transformación:
`sector` viene como `"Z10"` (zona numerada) o el municipio en MAYÚSCULAS
sin la palabra "Zona" (`"VILLA NUEVA"`). Regla aplicada en
`silver_tu_paradas.sql`: si matchea `^Z[0-9]+$` se expande a `"Zona N"`; si
no, se pasa a Título (`"Villa Nueva"`).

**Identidad del usuario — sin solución perfecta (advertencia del propio
enunciado):** no existe ninguna tabla que relacione las cuatro tarjetas de
un mismo pasajero. Estrategia adoptada: `usuario_key = operador || ':' ||
llave_nativa` (ej. `TRANSMETRO:TC-00013132`). Es una aproximación
**declarada, no una identidad de persona**. Límite explícito: un pasajero
con tarjeta de Transmetro y de Transurbano aparece como dos usuarios
distintos en `dim_usuario`; el análisis de transbordo real (Fase 2)
tendría que inferirse con una heurística espacio-temporal (ver "Extras"
del enunciado: Análisis de transbordo), no viene resuelto en Fase 1.

**Reglas de calidad → cuarentena** (`silver_cuarentena.sql`, nunca se
descarta en silencio):

| Motivo | Fuente | Regla |
|---|---|---|
| `duplicado_torniquete` | Transmetro | mismo `validacion_id` repetido |
| `fecha_futura` | Transmetro / Transurbano | `fecha_hora` posterior al momento de la carga |
| `parada_nula` | Transurbano | `cod_parada` vacío |
| `viaje_sin_salida` | MetroRiel | `exit` nulo, el pasajero no validó salida |
| `transaccion_no_exitosa` | Transurbano | `cod_estado` distinto de OK (1/2/3) — **no es defecto del dato**, es una decisión de negocio: un intento rechazado por el validador no es un abordaje real, pero se cuenta igual para que nunca se pierda en silencio |

**SCD Tipo 2 del padrón:** `silver_padron_transmetro_scd2.sql` abre una
versión nueva por cada evento del CDC (`valid_from`/`valid_to`), incluidos
los `DELETE` (que cierran la versión anterior y abren una versión
`INACTIVO`).

## 5. Diseño dimensional y Gold (1.4)

**Grano de `fact_abordaje` (tabla de hechos principal):** *un abordaje —
un usuario accede a un modo en una estación/parada en un momento dado.*

Se eligió este grano y no "un viaje puerta a puerta" porque tres de los
cuatro operadores (Transmetro, Transurbano, Aerómetro) solo registran el
acceso, nunca el cierre del viaje; inferir un cierre para ellos (¿dónde se
bajó el pasajero?) exigiría suponer datos que el operador nunca entregó.
Para MetroRiel, que sí cierra el viaje, se usa el evento de **entrada**
como su fila en `fact_abordaje` (así los cuatro operadores comparten
grano) — la información de cierre (estación de salida, duración) no se
descarta, vive en la segunda tabla de hechos.

**`fact_viaje_metroriel`** (segunda tabla de hechos, grano distinto): *un
viaje completo puerta a puerta.* Solo existe para MetroRiel porque es el
único operador que cierra el viaje en el mismo registro. Alimenta
directamente el "caso MetroRiel" del tablero de Fase 2 (trazado vs.
demanda en zonas 12-8-1-6-17).

**Matriz del bus:** ver `docs/matriz_bus.md`.

**Clasificación de medidas:**

| Medida | Tipo | Por qué |
|---|---|---|
| `monto_gtq` | Aditiva | Suma correctamente en cualquier dimensión (total recaudado por zona, por hora, por operador) |
| conteo de abordajes/viajes | Aditiva | Un conteo de filas siempre se puede sumar |
| `duracion_s` (MetroRiel) | No aditiva | Sumar duraciones de viajes distintos no tiene significado de negocio; solo se promedia o se toma percentil |
| `es_transbordo` | No aditiva (categórica) | Es una bandera, se cuenta o se filtra, no se suma con sentido propio más allá de un conteo |
| `hora_pico` / `dia_habil` (atributos de `dim_tiempo`) | No son medidas | Son atributos de la dimensión tiempo, no hechos |

## 6. Orquestación e idempotencia (1.5)

`orquestacion/flow_prefect.py` encadena: ingesta a Bronze → `dbt run`
(staging → silver → gold) → `dbt test`. Es idempotente porque:

- Bronze sobreescribe el archivo Parquet de la partición del día
  (`fecha_ingesta=YYYY-MM-DD/part-000.parquet`) en cada corrida del mismo
  día — no acumula copias.
- Silver y Gold son tablas (`materialized: table` en dbt) recalculadas
  por completo desde Bronze en cada corrida — no hay `INSERT` incremental
  que pueda duplicar.

Evidencia de las dos corridas: `docs/evidencia_idempotencia.json`
(conteos idénticos en las 13 tablas comparadas, capa por capa).

## 7. Pendiente para Fase 2 / gobernanza

- Seudonimizar `llave_nativa` antes de Gold (3.3) — hoy `dim_usuario`
  guarda la tarjeta en claro; falta hashear antes de exponerla a Tableau.
- Diccionario de datos formal de Gold, definiciones oficiales con dueño
  (3.1).
- Tablero en Tableau, recomendación y tabla de features (Fase 2).
