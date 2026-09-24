# Métricas medidas - Fase 1

## Volumen

Filas por fuente en Bronze contra Silver ya limpio:

| Fuente | Bronze | Silver |
|---|---:|---:|
| Transmetro validaciones | 363,221 | 362,106 |
| Transurbano transacciones | 832,791 | 786,398 |
| MetroRiel viajes | 299,100 | 295,511 |
| Aerómetro boardings | 203,554 | 203,554 |
| CDC padrón usuarios | 31,050 | ver sección CDC |

Filas en Gold: dim_zona 15, dim_operador 4, dim_estacion 468, dim_usuario
117,203, dim_tiempo 1,075 horas, fact_abordaje 1,647,569, y
fact_viaje_metroriel 295,511.

## Calidad

La cuarentena tiene 51,100 filas en total:

| Motivo | Fuente | Filas | % del total |
|---|---|---:|---:|
| transaccion_no_exitosa | Transurbano | 41,390 | 81.0% |
| parada_nula | Transurbano | 4,189 | 8.2% |
| viaje_sin_salida | MetroRiel | 3,589 | 7.0% |
| duplicado_torniquete | Transmetro | 1,115 | 2.2% |
| fecha_futura | Transurbano | 817 | 1.6% |

El motivo transaccion_no_exitosa domina porque agrupa toda transacción
rechazada por el validador, saldo insuficiente o tarjeta inválida, que en
el generador es alrededor del 15% de Transurbano por diseño. Como se
explica en decisiones.md, esto es una decisión de negocio y no un
defecto de captura.

## CDC del padrón de Transmetro

De las 31,050 filas del archivo CDC, 22,326 tienen llave con formato
Transmetro (71.9%). El resto queda fuera del padrón declarado: 5,223 con
formato Transurbano, 2,206 con SIN-TARJETA, y 1,295 con formato MetroRiel.

De esas 22,326 filas de Transmetro: 7,731 son INSERT, 11,675 son UPDATE y
2,920 son DELETE.

El padrón vigente de Transmetro termina con 17,432 tarjetas distintas,
de las cuales 15,096 quedan activas y 2,336 dadas de baja.

## Rendimiento

La ingesta completa a Bronze (streaming simulado más batch más CDC,
alrededor de 1.7 millones de filas de origen) tomó unos 80 segundos en la
primera corrida. El dbt run completo, con 13 vistas de staging, 7 tablas
de silver y 7 de gold, tomó unos 4 segundos. Las 13 pruebas de dbt test
corrieron en menos de medio segundo.

En disco, Bronze en Parquet ocupa 30.3 MB y warehouse.duckdb, con
staging, silver y gold materializados, ocupa 130.8 MB. El tiempo de
consulta del tablero todavía no se puede medir porque Tableau no está
conectado.

## Idempotencia

En docs/evidencia_idempotencia.json quedaron los conteos de las 13 tablas
comparadas entre la primera y la segunda corrida del pipeline completo el
mismo día, y son idénticos en las 13.

## Cobertura

dim_zona tiene 15 zonas o municipios con al menos una estación o parada
de algún operador: Mixco, San Miguel Petapa, Villa Nueva, y las zonas
numeradas 1, 4, 6, 7, 8, 9, 10, 11, 12, 13, 17 y 18. Guatemala tiene 25
zonas numeradas, así que 13 de ellas (2, 3, 5, 14, 15, 16, 19, 20, 21, 22,
23, 24 y 25) no tienen ninguna estación de ningún operador en este
dataset, lo cual es un buen candidato a corredor descubierto para la
recomendación de Fase 2.

No se puede calcular todavía cuántos usuarios usan más de un modo, porque
dim_usuario no unifica identidad entre operadores, como se explica en
decisiones.md. Eso necesitaría la heurística de transbordo que el
enunciado deja como extra opcional, o una fuente de identidad que hoy no
existe.
