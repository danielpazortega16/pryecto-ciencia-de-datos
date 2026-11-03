-- Todos los eventos del CDC del padron, con la llave numerica que vincula
-- la tarjeta a una persona (mismo supuesto que dim_usuario: el numero dentro
-- de TC-########, ########## y MR####### es la misma persona). Lo usa el
-- Proyecto 2 para saber si una persona tenia una baja aplicada antes de un
-- corte y cual era su perfil en ese momento.
select
    seq,
    commit_ts,
    op,
    tarjeta,
    operador_detectado,
    case
        when operador_detectado in ('TRANSMETRO', 'TRANSURBANO', 'METRORIEL')
        then cast(regexp_extract(tarjeta, '[0-9]+') as bigint)
    end as numero,
    perfil,
    zona_residencia,
    estado
from {{ ref('stg_cdc_padron_raw') }}
