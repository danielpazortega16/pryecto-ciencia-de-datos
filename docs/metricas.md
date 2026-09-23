# Métricas medidas — Fase 1

## Volumen (filas por capa)

| Fuente | Bronze | Silver (limpio) |
|---|---:|---:|
| Transmetro validaciones | 363,221 | 362,106 |
| Transurbano transacciones | 832,791 | 786,398 |
| MetroRiel viajes | 299,100 | 295,511 |
| Aerómetro boardings | 203,554 | 203,554 |
| CDC padrón usuarios | 31,050 | — (ver CDC abajo) |

| Gold | Filas |
|---|---:|
| dim_zona | 15 |
| dim_operador | 4 |
| dim_estacion | 468 |
| dim_usuario | 117,203 |
| dim_tiempo | 1,075 (horas) |
| fact_abordaje | 1,647,569 |
| fact_viaje_metroriel | 295,511 |

## Calidad (cuarentena, 51,100 filas totales)

| Motivo | Fuente | Filas | % del total cuarentena |
|---|---|---:|---:|
| transaccion_no_exitosa | Transurbano | 41,390 | 81.0% |
| parada_nula | Transurbano | 4,189 | 8.2% |
| viaje_sin_salida | MetroRiel | 3,589 | 7.0% |
| duplicado_torniquete | Transmetro | 1,115 | 2.2% |
| fecha_futura | Transurbano | 817 | 1.6% |

`transaccion_no_exitosa` es la mayoría porque agrupa **toda** transacción
rechazada por el validador (saldo insuficiente o tarjeta inválida, ~15% de
Transurbano por diseño del generador) — es una decisión de negocio, no un
defecto de captura (ver `docs/decisiones.md` sección 4).

## CDC (padrón de Transmetro)

- Eventos con llave formato Transmetro: 22,326 de 31,050 totales en el
  archivo (71.9%). El resto (5,223 formato Transurbano, 2,206
  `SIN-TARJETA`, 1,295 formato MetroRiel) queda fuera del padrón
  declarado de Transmetro — ver decisión en `docs/decisiones.md` §3.
- De esos 22,326: **7,731 INSERT, 11,675 UPDATE, 2,920 DELETE**.
- Tarjetas en el padrón vigente de Transmetro: **17,432** distintas.
  - **ACTIVAS: 15,096**
  - **INACTIVAS (dadas de baja): 2,336**

## Rendimiento

| Etapa | Duración medida |
|---|---:|
| Ingesta a Bronze (streaming simulado + batch + CDC, ~1.7M filas origen) | ~80 s (primera corrida) |
| `dbt run` completo (13 vistas Staging + 7 tablas Silver + 7 tablas Gold) | ~4 s |
| `dbt test` (13 pruebas unique/not_null) | ~0.4 s |

| Tamaño en disco | |
|---|---:|
| Bronze (Parquet, particionado por fecha) | 30.3 MB |
| `warehouse.duckdb` (Staging vistas + Silver + Gold, tablas materializadas) | 130.8 MB |

Tiempo de consulta del tablero: pendiente de Fase 2 (Tableau aún no
conectado).

## Idempotencia

Ver `docs/evidencia_idempotencia.json`: las 13 tablas comparadas
(Staging, Silver, Gold) tienen **conteos idénticos** entre la corrida 1 y
la corrida 2 del pipeline completo (ingesta + dbt run) el mismo día.

## Cobertura (parcial — se completa en Fase 2 con el tablero)

Zonas con al menos una estación/parada de algún operador (`dim_zona`,
15 zonas/municipios): Mixco, San Miguel Petapa, Villa Nueva, y las zonas
numeradas 1, 4, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18.

Guatemala tiene 25 zonas numeradas; **13 zonas (2, 3, 5, 14, 15, 16, 19,
20, 21, 22, 23, 24, 25) no tienen ninguna estación de ningún operador** en
este dataset — candidatas a "corredor descubierto" para la recomendación
de Fase 2.

Usuarios que usan más de un modo: no calculable de forma confiable en
Fase 1 porque `dim_usuario` no unifica identidad entre operadores (ver
límite declarado en `docs/decisiones.md` §4). Requiere la heurística de
transbordo (extra opcional) o una fuente de identidad que hoy no existe.
