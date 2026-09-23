-- Aerometro no trae reglas de calidad explicitas en el enunciado, pero se
-- deja la misma defensa de fecha futura por consistencia con las demas
-- fuentes de tiempo real.
select
    b.boarding_id,
    b.tarjeta_am,
    b.station_code,
    b.axis,
    b.fecha_hora_local as fecha_hora,
    b.monto_gtq,
    e.zona_canonica
from {{ ref('stg_am_boardings') }} b
left join {{ ref('stg_am_estaciones') }} e on e.station_code = b.station_code
where b.fecha_hora_local <= current_timestamp
