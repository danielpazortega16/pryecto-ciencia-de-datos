# Decisiones de diseño - Fase 1

## Datos de origen

Se usó el generar_red_metropolitana.py oficial del curso (60,000 usuarios,
45 días, ESCALA 0.08, semilla 2026). Antes de recibirlo había armado un
generador propio para no perder tiempo mientras llegaba el oficial
(quedó en docs/generador_sustituto_fase_inicial.py, ya no se usa para
nada, se descartó apenas llegó el real).

## Ingesta y vía por fuente

Transmetro (validaciones) y Aerómetro (boardings) entran por streaming
simulado con Kafka, porque en producción son eventos de torniquete o de
cabina que llegan continuamente. Los cuatro catálogos y los viajes de
MetroRiel entran por batch, porque los catálogos cambian rara vez y
MetroRiel entrega el viaje ya cerrado, no evento por evento. El padrón de
usuarios entra por CDC porque es el único archivo que se actualiza y se
borra, los demás solo crecen.

Transurbano quedaba a criterio del equipo y se decidió meterlo por batch.
El archivo trae fecha y hora en columnas separadas y el monto ya en
centavos, que es la forma típica de un extracto de liquidación
consolidado al cierre de un periodo, no de un evento que haya que
capturar en el instante en que ocurre. Meterlo por streaming solo
agregaría la complejidad de un tópico sin ganar nada, porque a la Agencia
no le sirve saber en tiempo real que alguien abordó un bus de Transurbano.
La consecuencia es que Transurbano siempre va a tener más latencia que
Transmetro o Aerómetro, lo cual es aceptable porque nada en la Fase 2
pide demanda de Transurbano en tiempo real.

Por la ventana de entrega no se levantó Kafka en Docker. El script
src/ingesta/ingesta_streaming.py simula productor, tópico y consumidor
leyendo el CSV línea por línea y publicando cada fila con una función
publicar_evento() que está aislada del resto del pipeline a propósito,
para poder cambiarla por un productor y consumidor reales sin tocar
Bronze ni lo que viene después.

Bronze vive en un lake de carpetas más Parquet particionado por fecha de
ingesta, no en el warehouse. La razón es que uno de los archivos
(MetroRiel) es JSON anidado, y forzarlo a una tabla relacional al
aterrizar solo para deshacer esa estructura en Silver es trabajo de más.
El warehouse en DuckDB arranca recién en Staging.

## Staging y CDC

El generador oficial mezcla a propósito los formatos de llave en la
columna tarjeta del CDC, con prioridad tm, tu, mr, o SIN-TARJETA si el
usuario no tiene ninguna. Es una ambigüedad intencional del curso: el
padrón que pide la consigna es "de Transmetro", pero el archivo trae
llaves de las cuatro.

Se decidió construir el padrón vigente de Transmetro solo con las filas
del CDC cuya llave cumple el formato TC-########. El resto queda
clasificado (se puede ver en stg_cdc_padron_raw.operador_detectado) pero
fuera del padrón declarado. No se armó un padrón "central" con todo
mezclado porque la consigna pide explícitamente el de Transmetro, y
mezclar target ambiguo con catálogos de otros operadores hubiera violado
la instrucción de no inventar datos que el operador no entregó.

De las filas del CDC, la mayoría sí son formato Transmetro; el resto
(formato Transurbano, SIN-TARJETA, formato MetroRiel) se excluye del
padrón por diseño, y los conteos exactos están en docs/metricas.md.

Los DELETE marcan la tarjeta como inactiva, nunca se borra la fila: se
conserva el perfil y la zona de residencia del último INSERT o UPDATE
conocido, porque el evento de borrado llega sin cuerpo.

Para Transurbano, MetroRiel y Aerómetro se armó un catálogo mínimo con
solo la llave distinta que aparece en su propio archivo de operación, sin
inventar nombre, fecha de alta ni ningún otro atributo que esos
operadores nunca entregaron.

## Capa Silver

Las fechas se llevaron a un timestamp único, Transurbano se convirtió de
centavos a quetzales dividiendo entre 100, y Aerómetro se pasó de UTC a
hora local restando 6 horas fijas (Guatemala no observa horario de
verano).

Transmetro, MetroRiel y Aerómetro ya entregan la zona en forma canónica
("Zona 10", "Mixco") por cómo el generador arma sus catálogos, así que no
necesitan transformación. Solo Transurbano la necesita: su columna sector
viene como "Z10" para zonas numeradas o como el municipio en mayúsculas
sin la palabra Zona, por ejemplo "VILLA NUEVA". En silver_tu_paradas.sql
se expande el primer caso a "Zona N" y el segundo se pasa a título
("Villa Nueva").

La identidad del usuario no tiene solución perfecta, y el propio
enunciado lo advierte: no existe ninguna tabla que relacione las cuatro
tarjetas de un mismo pasajero. La estrategia que se adoptó fue construir
la llave conformada como operador más dos puntos más llave nativa, por
ejemplo TRANSMETRO:TC-00013132. Es una aproximación declarada, no una
identidad de persona real, y su límite es explícito: un pasajero con
tarjeta de Transmetro y de Transurbano va a aparecer como dos usuarios
distintos en dim_usuario. Medir transbordo real necesitaría una
heurística espacio-temporal (el enunciado la menciona como extra
opcional) que no se resolvió en esta fase.

Las reglas de calidad se mandan a cuarentena en silver_cuarentena.sql y
nunca se descartan en silencio: duplicado de torniquete en Transmetro
cuando se repite el mismo validacion_id, fecha futura en Transmetro y
Transurbano cuando la fecha es posterior al momento de la carga, parada
nula en Transurbano cuando cod_parada viene vacío, y viaje sin salida en
MetroRiel cuando el pasajero no validó salida. Aparte de eso se agregó un
quinto motivo, transaccion_no_exitosa, para las transacciones de
Transurbano con código de estado distinto de OK: esto no es un defecto
del dato, es una decisión de negocio, porque un intento rechazado por el
validador no es un abordaje real, pero se cuenta igual para que nunca se
pierda sin dejar rastro.

El padrón se historizó con SCD tipo 2 en
silver_padron_transmetro_scd2.sql: cada evento del CDC abre una versión
nueva con su rango de vigencia, incluidos los DELETE, que cierran la
versión anterior y abren una versión marcada como inactiva.

## Diseño dimensional y Gold

El grano de fact_abordaje, la tabla de hechos principal, es un abordaje:
un usuario accede a un modo en una estación o parada en un momento dado.
Se eligió este grano y no "un viaje puerta a puerta" porque tres de los
cuatro operadores solo registran el acceso y nunca el cierre del viaje, e
inferir ese cierre exigiría suponer datos que el operador nunca entregó.
Para MetroRiel, que sí cierra el viaje, se usa el evento de entrada como
su fila en fact_abordaje, así los cuatro operadores comparten el mismo
grano, y la información de cierre no se pierde, vive en la segunda tabla
de hechos.

fact_viaje_metroriel tiene un grano distinto, un viaje completo puerta a
puerta, y solo existe para MetroRiel porque es el único operador que
cierra el viaje en el mismo registro. Esta tabla alimenta directamente el
caso MetroRiel del tablero de Fase 2, cuando haya que analizar si el
trazado atiende la demanda observada en las zonas 12, 8, 1, 6 y 17.

La matriz del bus está en docs/matriz_bus.md.

Sobre las medidas: monto_gtq y los conteos de abordajes o viajes son
aditivos, se pueden sumar en cualquier dimensión sin perder sentido.
duracion_s en MetroRiel no es aditiva, porque sumar duraciones de viajes
distintos no significa nada de negocio, solo se puede promediar. La
bandera es_transbordo tampoco es aditiva, es categórica, se cuenta o se
filtra. hora_pico y dia_habil no son medidas, son atributos de la
dimensión tiempo.

## Orquestación e idempotencia

orquestacion/flow_prefect.py encadena ingesta a Bronze, dbt run de
staging a silver a gold, y dbt test. Es idempotente porque Bronze
sobreescribe el Parquet de la partición del día en cada corrida, no
acumula copias, y porque Silver y Gold están materializados como tablas
que se recalculan por completo desde Bronze en cada corrida, sin ningún
insert incremental que pueda duplicar algo. La evidencia de dos corridas
con conteos idénticos en las 13 tablas comparadas está en
docs/evidencia_idempotencia.json.

## Pendiente para más adelante

Falta seudonimizar la llave nativa antes de Gold, porque hoy dim_usuario
guarda la tarjeta en claro y habría que hashearla antes de exponerla a
Tableau. Falta también el diccionario de datos formal de Gold con
definiciones oficiales y dueño asignado, y por supuesto todo lo de Fase
2: el tablero, la recomendación y la tabla de features.
