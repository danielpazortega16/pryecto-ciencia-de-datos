select
    cast(id_estacion as integer) as id_estacion,
    nombre_estacion,
    zona_nombre as zona_canonica,
    cast(km as double) as km
from {{ bronze_parquet('mr_estaciones') }}
