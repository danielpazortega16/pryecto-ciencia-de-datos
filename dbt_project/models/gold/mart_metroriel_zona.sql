-- Caso MetroRiel (2.1): demanda observada de los OTROS modos por zona contra
-- lo que MetroRiel atiende. Se usa la demanda de los otros tres operadores
-- como medida de necesidad porque MetroRiel solo mide donde ya llega.
with otros as (
    select zona_nombre, sum(abordajes) as abordajes_otros_modos
    from {{ ref('mart_demanda') }}
    where operador != 'METRORIEL'
    group by 1
),
mr as (
    select zona_nombre, sum(abordajes) as abordajes_metroriel
    from {{ ref('mart_demanda') }}
    where operador = 'METRORIEL'
    group by 1
)
select
    c.zona_nombre,
    c.zona_tipo,
    c.estaciones_metroriel,
    (c.estaciones_metroriel > 0) as en_trazado_metroriel,
    coalesce(o.abordajes_otros_modos, 0) as abordajes_otros_modos,
    coalesce(m.abordajes_metroriel, 0) as abordajes_metroriel,
    rank() over (order by coalesce(o.abordajes_otros_modos, 0) desc) as ranking_demanda_otros_modos
from {{ ref('mart_cobertura_zona') }} c
left join otros o on o.zona_nombre = c.zona_nombre
left join mr m on m.zona_nombre = c.zona_nombre
