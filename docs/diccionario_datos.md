# Diccionario de datos - capa Gold

Para cada campo: qué significa, de qué fuente sale y qué transformación
se le aplicó. Los nombres de fuente son los de los archivos originales.
El detalle de cómo se llega desde el archivo crudo a cada tabla está en
docs/linaje.md.

## dim_zona

Una fila por zona de la ciudad o municipio que tiene al menos una
estación o parada de algún operador.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| zona_key | Llave sustituta de la zona | Generada en Gold | row_number sobre el nombre de zona |
| zona_nombre | Nombre oficial de la zona ("Zona 10", "Mixco") | tm_estaciones.zona, mr_estaciones.zona_nombre, am_estaciones.district, tu_paradas.sector | Los tres primeros ya vienen así. En Transurbano "Z10" pasa a "Zona 10" y "VILLA NUEVA" a "Villa Nueva" |
| zona_tipo | ZONA_GUATEMALA o MUNICIPIO | Derivado | MUNICIPIO si el nombre no empieza con "Zona" |

## dim_operador

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| operador | Código del operador (TRANSMETRO, TRANSURBANO, METRORIEL, AEROMETRO) | Constante | Ninguna |
| nombre | Nombre comercial | Constante | Ninguna |
| modo | Tipo de transporte | Constante | Ninguna |
| unidades_infra | Líneas, rutas o ejes del operador | Cifras del enunciado | 8 líneas, 41 rutas, 1 línea, 2 ejes |

## dim_estacion

Una fila por estación o parada de cualquier operador.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| estacion_key | Llave sustituta | Generada en Gold | row_number por operador y código |
| operador | A qué operador pertenece | Catálogo de origen | Constante por catálogo |
| codigo_nativo | Código con que el operador la identifica | tm_estaciones.estacion_id, tu_paradas.cod_parada, mr_estaciones.id_estacion, am_estaciones.station_code | Se pasa a texto |
| nombre | Nombre de la estación o parada | nombre, descripcion, nombre_estacion, station_name | Ninguna |
| zona_key | Zona donde está | Catálogo de origen | Unión con dim_zona por nombre conformado |
| lat, lon | Coordenadas | Solo tm_estaciones | Nulas para los otros tres operadores, que no las entregan |

## dim_tiempo

Una fila por hora, entre la primera y la última hora con eventos.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| tiempo_key | Llave con formato AAAAMMDDHH | Generada | strftime del inicio de la hora |
| fecha | Día calendario | Generada | Ninguna |
| hora_del_dia | Hora de 0 a 23 | Generada | Ninguna |
| dia_habil | Verdadero de lunes a viernes | Generada | No considera feriados |
| hora_pico | Verdadero entre 5 y 8 y entre 16 y 19 | Generada | Macro es_hora_pico, la misma que usa la tabla de features |

## dim_usuario

Una fila por tarjeta de cada operador. No contiene la tarjeta en claro.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| usuario_key | Seudónimo de la tarjeta de un operador | Tarjeta de cada archivo de operación | sha256 de sal, operador y tarjeta, primeros 16 caracteres |
| operador | Operador al que pertenece la tarjeta | Archivo de operación | Constante |
| perfil | estudiante, trabajador, adulto_mayor o general | cdc_padron_usuarios.perfil | Solo existe para tarjetas de Transmetro con alta en el CDC; el resto queda nulo |
| zona_residencia | Zona de residencia declarada | cdc_padron_usuarios.zona_residencia | Igual que perfil |
| estado_padron | ACTIVO, INACTIVO o SIN_PADRON | cdc_padron_usuarios.op | ACTIVO o INACTIVO según el último evento; SIN_PADRON si nunca hubo alta; nulo para los otros operadores, que no tienen padrón |
| persona_key | Seudónimo de la persona | Número dentro de la tarjeta | Supuesto declarado: el número de TC-########, 0000000### y MR####### identifica a la misma persona. Aerómetro no se puede vincular |
| vinculo_persona | NUMERO_TARJETA o SIN_VINCULO | Derivado | Indica si persona_key salió del supuesto anterior |

## fact_abordaje

Grano: un abordaje, es decir un usuario que accede a un modo en una
estación o parada en un momento dado.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| abordaje_key | Identificador del abordaje | validacion_id, id de transacción, trip_id, boarding_id | Operador más dos puntos más el id de origen. En Transurbano el id lo genera Staging porque el archivo no trae |
| operador | Operador del abordaje | Archivo de operación | Constante |
| usuario_key | Seudónimo de la tarjeta | tarjeta, num_tarjeta, card, user_hash | Igual que en dim_usuario |
| estacion_key | Estación o parada donde ocurrió | estacion_id, cod_parada, entry.station, station_code | Unión con dim_estacion |
| tiempo_key | Hora del abordaje | fecha_hora, fecha y hora, entry.ts, timestamp_utc | Se trunca a la hora. Aerómetro se pasa de UTC a hora local restando 6 horas |
| fecha_hora | Momento exacto del abordaje | Igual que arriba | Timestamp único para los cuatro operadores |
| monto_gtq | Tarifa cobrada en quetzales | tarifa, monto_centavos, fare_gtq, fare | Transurbano se divide entre 100 |
| es_transbordo | Marca de transbordo | transmetro_validaciones.tipo | Verdadero si tipo = TRANSBORDO. Solo Transmetro lo informa; en los demás es falso por falta de dato |

Para MetroRiel se usa la entrada del viaje como abordaje.

## fact_viaje_metroriel

Grano: un viaje completo de MetroRiel, con entrada y salida validadas.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| viaje_id | Identificador del viaje | metroriel_viajes.trip_id | Ninguna |
| usuario_key | Seudónimo de la tarjeta | card | Igual que en dim_usuario |
| estacion_origen_key | Estación de entrada | entry.station | Unión con dim_estacion |
| estacion_destino_key | Estación de salida | exit.station | Unión con dim_estacion |
| tiempo_key_entrada | Hora de entrada | entry.ts | Se trunca a la hora |
| ts_entrada, ts_salida | Momento de entrada y de salida | entry.ts, exit.ts | Ninguna |
| duracion_s | Duración del viaje en segundos | duration_s | Ninguna |
| monto_gtq | Tarifa en quetzales | fare_gtq | Ninguna |

Los viajes sin salida no llegan aquí, están en silver_cuarentena.

## Tablas resumen para el tablero

Se calculan a partir de las tablas anteriores y son lo que lee Tableau.

mart_demanda: abordajes y recaudo por fecha, hora, operador y zona.
mart_cobertura_zona: por cada una de las 25 zonas y los municipios, cuántas
estaciones tiene de cada operador y cuántos modos la sirven.
mart_transbordo: personas según en cuántos operadores aparecen (depende del
supuesto de persona_key).
mart_metroriel_zona: por zona, demanda de los otros tres modos contra
abordajes de MetroRiel y si la zona está en el trazado.
mart_metroriel_od: viajes de MetroRiel por estación de origen y destino.
