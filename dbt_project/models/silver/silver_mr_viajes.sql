-- Regla de calidad: viajes sin salida (el pasajero no valido al bajar)
-- van a cuarentena, no se puede cerrar el viaje sin estacion de destino.
select
    v.viaje_id,
    v.tarjeta_mr,
    v.estacion_entrada,
    v.ts_entrada,
    v.estacion_salida,
    v.ts_salida,
    v.monto_gtq,
    v.duracion_s,
    eo.zona_canonica as zona_entrada,
    ed.zona_canonica as zona_salida
from {{ ref('stg_mr_viajes') }} v
left join {{ ref('stg_mr_estaciones') }} eo on eo.id_estacion = v.estacion_entrada
left join {{ ref('stg_mr_estaciones') }} ed on ed.id_estacion = v.estacion_salida
where not v.sin_salida
