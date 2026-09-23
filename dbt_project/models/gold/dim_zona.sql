-- Dimension conformada de zona: une los catalogos de los 4 operadores
-- una vez que Silver ya tradujo "Z10"/"VILLA NUEVA" a la misma forma que
-- usan Transmetro, MetroRiel y Aerometro ("Zona 10", "Villa Nueva").
with zonas as (
    select distinct zona_canonica from {{ ref('stg_tm_estaciones') }}
    union
    select distinct zona_canonica from {{ ref('silver_tu_paradas') }}
    union
    select distinct zona_canonica from {{ ref('stg_mr_estaciones') }}
    union
    select distinct zona_canonica from {{ ref('stg_am_estaciones') }}
)
select
    row_number() over (order by zona_canonica) as zona_key,
    zona_canonica as zona_nombre,
    case when zona_canonica like 'Zona %' then 'ZONA_GUATEMALA' else 'MUNICIPIO' end as zona_tipo
from zonas
where zona_canonica is not null
