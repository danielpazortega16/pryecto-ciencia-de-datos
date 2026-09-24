select
    cast(boarding_id as bigint) as boarding_id,
    user_hash as tarjeta_am,
    station_code,
    axis,
    strptime(timestamp_utc, '%Y-%m-%dT%H:%M:%SZ') as ts_utc,
    -- Aerometro entrega UTC, no hora local. Guatemala = UTC-6 todo el ano
    -- (no observa horario de verano), resta fija sin tabla de zonas horarias.
    strptime(timestamp_utc, '%Y-%m-%dT%H:%M:%SZ') - interval '6 hours' as fecha_hora_local,
    cast(cabin_number as integer) as cabin_number,
    cast(fare as double) as monto_gtq
from {{ bronze_parquet('am_boardings') }}
