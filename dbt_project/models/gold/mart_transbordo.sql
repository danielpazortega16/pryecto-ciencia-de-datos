-- Transbordo (2.1): personas segun en cuantos operadores aparecen. Depende
-- del supuesto de vinculo por numero de tarjeta (ver dim_usuario): es una
-- cota basada en un supuesto, no una medicion directa.
with por_persona as (
    select
        u.persona_key,
        count(distinct f.operador) as n_operadores,
        string_agg(distinct f.operador, ' + ' order by f.operador) as combinacion
    from {{ ref('fact_abordaje') }} f
    join {{ ref('dim_usuario') }} u on u.usuario_key = f.usuario_key
    group by 1
)
select
    n_operadores,
    combinacion,
    count(*) as personas
from por_persona
group by 1, 2
