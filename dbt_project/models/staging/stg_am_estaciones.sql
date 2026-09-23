select
    station_code,
    station_name,
    axis,
    district as zona_canonica  -- ya viene canonico: "Mixco", "Zona 7", etc.
from {{ source('bronze', 'am_estaciones') }}
