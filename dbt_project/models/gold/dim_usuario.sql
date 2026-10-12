-- Estrategia de identidad (ver docs/decisiones.md). No existe tabla que
-- relacione las tarjetas de un mismo pasajero, asi que hay dos niveles:
--   usuario_key: una llave por (operador, tarjeta), seudonimizada con
--     sha256 + sal. Es la identidad "segura": nunca junta dos tarjetas.
--   persona_key: supuesto declarado, no hecho verificable. Para Transmetro,
--     Transurbano y MetroRiel se asume que el numero dentro de la tarjeta
--     (TC-00013132, 0000013132, MR0013132) identifica a la misma persona.
--     Aerometro entrega un hash opaco y no se puede vincular.
-- La tarjeta en claro no sale de Silver: Gold solo guarda seudonimos.
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
    {{ pseudonimo('operador', 'llave_nativa') }} as usuario_key,
    operador,
    perfil,
    zona_residencia,
    estado_padron,
    case
        when operador in ('TRANSMETRO', 'TRANSURBANO', 'METRORIEL')
        then {{ pseudonimo("'PERSONA'", "cast(cast(regexp_extract(llave_nativa, '[0-9]+') as bigint) as varchar)") }}
        else {{ pseudonimo('operador', 'llave_nativa') }}
    end as persona_key,
    case
        when operador in ('TRANSMETRO', 'TRANSURBANO', 'METRORIEL') then 'NUMERO_TARJETA'
        else 'SIN_VINCULO'
    end as vinculo_persona
from todos
