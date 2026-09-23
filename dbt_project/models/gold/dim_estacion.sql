-- Dimension conformada de estacion/parada. Grano: una fila por
-- (operador, codigo nativo). lat/lon solo existen para Transmetro.
with todas as (
    select 'TRANSMETRO' as operador, estacion_id as codigo_nativo, nombre, zona_canonica, lat, lon
    from {{ ref('stg_tm_estaciones') }}
    union all
    select 'TRANSURBANO', cod_parada, descripcion, zona_canonica, cast(null as double), cast(null as double)
    from {{ ref('silver_tu_paradas') }}
    union all
    select 'METRORIEL', cast(id_estacion as varchar), nombre_estacion, zona_canonica, cast(null as double), cast(null as double)
    from {{ ref('stg_mr_estaciones') }}
    union all
    select 'AEROMETRO', station_code, station_name, zona_canonica, cast(null as double), cast(null as double)
    from {{ ref('stg_am_estaciones') }}
)
select
    row_number() over (order by operador, codigo_nativo) as estacion_key,
    t.operador,
    t.codigo_nativo,
    t.nombre,
    z.zona_key,
    t.lat,
    t.lon
from todas t
left join {{ ref('dim_zona') }} z on z.zona_nombre = t.zona_canonica
