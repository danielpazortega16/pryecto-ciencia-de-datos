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

La ingesta completa a Bronze (streaming simulado, batch y CDC, alrededor
de 1.7 millones de filas de origen) toma unos 1.2 segundos. La
primera versión, que movía el streaming fila por fila en Python, tomaba
unos 80. El dbt run completo (13 vistas de staging, 7 tablas de silver, 12
de gold y la de features) toma entre 10 y 24 segundos según la máquina. Las
pruebas de dbt test corren en menos de 2 segundos.

En disco, Bronze en Parquet ocupa 56 MB con dos cargas acumuladas (una
por día) y warehouse.duckdb, con silver, gold y features, ocupa 138 MB. Una
consulta de las que usa el tablero sobre mart_demanda tarda unos 3
milisegundos, y una agregación directa sobre fact_abordaje (1.6 millones
de filas) unos 15.

## Idempotencia

En docs/evidencia_idempotencia.json están los conteos de 20 tablas
(silver, gold y features) en dos corridas completas con dos cargas de días
distintos en Bronze, y son idénticos en las 20. Se puede repetir con
python src/ingesta/verificar_idempotencia.py.

## Cobertura

dim_zona tiene 15 zonas o municipios con al menos una estación o parada
de algún operador: Mixco, San Miguel Petapa, Villa Nueva, y las zonas
numeradas 1, 4, 6, 7, 8, 9, 10, 11, 12, 13, 17 y 18. Tres de ellas (1, 12 y
17) tienen los cuatro operadores. Guatemala tiene 25 zonas numeradas, así
que 13 (2, 3, 5, 14, 15, 16, 19, 20, 21, 22, 23, 24 y 25) no tienen ninguna
estación de ningún operador. Está en mart_cobertura_zona.

Usuarios que usan más de un modo: 36,827 de 70,380 personas (52.3%), de
las cuales 9,996 usan tres, siempre bajo el supuesto de que el número
dentro de la tarjeta identifica a la misma persona (ver decisiones.md). Es
una cota basada en un supuesto, no una medición directa. Está en
mart_transbordo.
