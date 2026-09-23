-- 1.2 Staging y CDC: padron vigente de Transmetro.
-- Alcance declarado: solo filas del CDC cuya llave es formato Transmetro
-- (TC-########). Las demas (SIN-TARJETA, formato TU/MR) no pertenecen a
-- este padron -- ver stg_cdc_padron_raw y docs/decisiones.md para el conteo
-- y la justificacion de por que se excluyen aqui.
with eventos_tm as (
    select * from {{ ref('stg_cdc_padron_raw') }}
    where operador_detectado = 'TRANSMETRO'
),
ultimo_evento as (
    select *, row_number() over (partition by tarjeta order by seq desc) as rn
    from eventos_tm
),
ultimo_dato_conocido as (
    select tarjeta, perfil, zona_residencia,
           row_number() over (partition by tarjeta order by seq desc) as rn
    from eventos_tm
    where op in ('INSERT', 'UPDATE')
)
select
    u.tarjeta as tarjeta_tm,
    d.perfil,
    d.zona_residencia,
    case when u.op = 'DELETE' then 'INACTIVO' else 'ACTIVO' end as estado_vigente,
    u.commit_ts as ultimo_cambio_ts,
    u.op as ultima_operacion,
    u.seq as ultimo_seq
from ultimo_evento u
left join ultimo_dato_conocido d on d.tarjeta = u.tarjeta and d.rn = 1
where u.rn = 1
