-- Historiza el padron de Transmetro (SCD Tipo 2): cada cambio de estado o
-- de atributo abre una version nueva con su rango de vigencia. Los DELETE
-- cierran la version anterior y abren una version INACTIVO (no se borra
-- el historial de la tarjeta).
with eventos as (
    select
        tarjeta,
        seq,
        commit_ts,
        op,
        -- un DELETE llega sin cuerpo: se arrastra el ultimo perfil/zona
        -- conocido para no perder el atributo en la version cerrada
        coalesce(perfil, last_value(perfil ignore nulls) over (
            partition by tarjeta order by seq
            rows between unbounded preceding and current row
        )) as perfil,
        coalesce(zona_residencia, last_value(zona_residencia ignore nulls) over (
            partition by tarjeta order by seq
            rows between unbounded preceding and current row
        )) as zona_residencia,
        case when op = 'DELETE' then 'INACTIVO' else 'ACTIVO' end as estado
    from {{ ref('stg_cdc_padron_raw') }}
    where operador_detectado = 'TRANSMETRO'
)
select
    tarjeta as tarjeta_tm,
    perfil,
    zona_residencia,
    estado,
    op as operacion_origen,
    seq,
    commit_ts as valid_from,
    lead(commit_ts) over (partition by tarjeta order by seq) as valid_to,
    (row_number() over (partition by tarjeta order by seq desc) = 1) as es_version_vigente
from eventos
