-- Segunda tabla de hechos, grano distinto: UN VIAJE COMPLETO puerta a
-- puerta. Solo existe para MetroRiel, el unico operador que cierra el
-- viaje (entrada+salida) en el mismo registro. Alimenta el "caso
-- MetroRiel" del tablero (Fase 2): analizar si el trazado atiende la
-- demanda observada en las zonas 12, 8, 1, 6 y 17.
select
    v.viaje_id,
    'METRORIEL:' || v.tarjeta_mr as usuario_key,
    eo.estacion_key as estacion_origen_key,
    ed.estacion_key as estacion_destino_key,
    cast(strftime(v.ts_entrada, '%Y%m%d%H') as bigint) as tiempo_key_entrada,
    v.ts_entrada,
    v.ts_salida,
    v.duracion_s,
    v.monto_gtq
from {{ ref('silver_mr_viajes') }} v
left join {{ ref('dim_estacion') }} eo
    on eo.operador = 'METRORIEL' and eo.codigo_nativo = cast(v.estacion_entrada as varchar)
left join {{ ref('dim_estacion') }} ed
    on ed.operador = 'METRORIEL' and ed.codigo_nativo = cast(v.estacion_salida as varchar)
