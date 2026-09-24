-- El generador oficial mezcla formatos de llave en la columna "tarjeta"
-- del CDC (prioridad tm > tu > mr, o "SIN-TARJETA"): es ambiguedad
-- intencional del enunciado (ver docs/decisiones.md). Aqui solo se
-- tipa el evento; la decision de a que padron pertenece cada fila se
-- resuelve en los modelos siguientes.
select
    cast(seq as bigint) as seq,
    cast(commit_ts as timestamp) as commit_ts,
    op,
    tarjeta,
    nullif(perfil, '') as perfil,
    nullif(zona_residencia, '') as zona_residencia,
    nullif(estado, '') as estado,
    case
        when tarjeta like 'TC-%' then 'TRANSMETRO'
        when tarjeta like 'MR%' then 'METRORIEL'
        when tarjeta similar to '[0-9]{10}' then 'TRANSURBANO'
        when tarjeta = 'SIN-TARJETA' then 'SIN_TARJETA'
        else 'DESCONOCIDO'
    end as operador_detectado
from {{ bronze_parquet('cdc_padron_usuarios') }}
