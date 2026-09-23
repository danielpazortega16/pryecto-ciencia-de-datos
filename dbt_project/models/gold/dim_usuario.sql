-- Estrategia de identidad (ver docs/decisiones.md): no existe crosswalk
-- entre las 4 tarjetas de un mismo pasajero, asi que la llave conformada
-- es por operador: usuario_key = operador || ':' || llave_nativa. Esto es
-- una aproximacion declarada, no una identidad de persona; el limite es
-- que un pasajero con tarjeta de dos sistemas aparece aqui como dos
-- usuarios distintos.
with tm as (
    select
        'TRANSMETRO' as operador,
        u.tarjeta_tm as llave_nativa,
        p.perfil,
        p.zona_residencia,
        coalesce(p.estado_vigente, 'SIN_PADRON') as estado_padron
    from (select distinct tarjeta_tm from {{ ref('silver_tm_validaciones') }}) u
    left join {{ ref('stg_padron_transmetro_vigente') }} p on p.tarjeta_tm = u.tarjeta_tm
),
tu as (
    select 'TRANSURBANO' as operador, tarjeta_tu as llave_nativa,
           cast(null as varchar) as perfil, cast(null as varchar) as zona_residencia,
           cast(null as varchar) as estado_padron
    from {{ ref('stg_catalogo_usuarios_tu') }}
),
mr as (
    select 'METRORIEL' as operador, tarjeta_mr as llave_nativa,
           cast(null as varchar) as perfil, cast(null as varchar) as zona_residencia,
           cast(null as varchar) as estado_padron
    from {{ ref('stg_catalogo_usuarios_mr') }}
),
am as (
    select 'AEROMETRO' as operador, tarjeta_am as llave_nativa,
           cast(null as varchar) as perfil, cast(null as varchar) as zona_residencia,
           cast(null as varchar) as estado_padron
    from {{ ref('stg_catalogo_usuarios_am') }}
),
todos as (
    select * from tm union all select * from tu
    union all select * from mr union all select * from am
)
select
    operador || ':' || llave_nativa as usuario_key,
    operador,
    llave_nativa,
    perfil,
    zona_residencia,
    estado_padron
from todos
