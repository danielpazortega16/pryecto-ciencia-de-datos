select
    estacion_id,
    nombre,
    linea,
    zona as zona_canonica,  -- Transmetro ya usa "Zona N" / municipio, sin transformar
    cast(lat as double) as lat,
    cast(lon as double) as lon
from {{ bronze_parquet('tm_estaciones') }}
