-- MetroRiel entrega el viaje completo como JSON anidado (entry/exit son
-- structs). Aqui se aplana; exit puede venir null (viaje sin cerrar).
select
    cast(trip_id as bigint) as viaje_id,
    card as tarjeta_mr,
    cast(entry.station as integer) as estacion_entrada,
    cast(entry.ts as timestamp) as ts_entrada,
    cast(exit.station as integer) as estacion_salida,
    cast(exit.ts as timestamp) as ts_salida,
    cast(fare_gtq as double) as monto_gtq,
    cast(duration_s as integer) as duracion_s,
    (exit is null) as sin_salida
from {{ bronze_parquet('mr_viajes') }}
