-- Cobertura (2.1): el universo son las 25 zonas de la ciudad mas los
-- municipios que aparecen en algun catalogo. Una zona sin estacion de ningun
-- operador queda con n_modos_con_servicio = 0.
with universo as (
    select 'Zona ' || n as zona_nombre, 'ZONA_GUATEMALA' as zona_tipo
    from (select unnest(range(1, 26)) as n)
    union
    select zona_nombre, zona_tipo from {{ ref('dim_zona') }} where zona_tipo = 'MUNICIPIO'
),
estaciones as (
    select z.zona_nombre,
           count(*) filter (where e.operador = 'TRANSMETRO')  as estaciones_transmetro,
           count(*) filter (where e.operador = 'TRANSURBANO') as paradas_transurbano,
           count(*) filter (where e.operador = 'METRORIEL')   as estaciones_metroriel,
           count(*) filter (where e.operador = 'AEROMETRO')   as estaciones_aerometro
    from {{ ref('dim_estacion') }} e
    join {{ ref('dim_zona') }} z on z.zona_key = e.zona_key
    group by 1
),
demanda as (
    select zona_nombre, sum(abordajes) as abordajes_total
    from {{ ref('mart_demanda') }}
    group by 1
)
select
    u.zona_nombre,
    u.zona_tipo,
    coalesce(s.estaciones_transmetro, 0) as estaciones_transmetro,
    coalesce(s.paradas_transurbano, 0) as paradas_transurbano,
    coalesce(s.estaciones_metroriel, 0) as estaciones_metroriel,
    coalesce(s.estaciones_aerometro, 0) as estaciones_aerometro,
    (cast(coalesce(s.estaciones_transmetro, 0) > 0 as int)
     + cast(coalesce(s.paradas_transurbano, 0) > 0 as int)
     + cast(coalesce(s.estaciones_metroriel, 0) > 0 as int)
     + cast(coalesce(s.estaciones_aerometro, 0) > 0 as int)) as n_modos_con_servicio,
    coalesce(d.abordajes_total, 0) as abordajes_total
from universo u
left join estaciones s on s.zona_nombre = u.zona_nombre
left join demanda d on d.zona_nombre = u.zona_nombre
