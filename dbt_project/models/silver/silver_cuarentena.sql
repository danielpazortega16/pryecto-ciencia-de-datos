-- Tabla unica de cuarentena: los registros malos se conservan con su
-- motivo de rechazo, nunca se descartan en silencio (penalizacion 1.3).
with tm_duplicados as (
    select
        'TRANSMETRO' as fuente,
        cast(validacion_id as varchar) as id_registro,
        'duplicado_torniquete' as motivo,
        'validacion_id repetido en la misma lectura de torniquete' as detalle,
        fecha_hora as fecha_hora_evento
    from (
        select *, row_number() over (partition by validacion_id order by fecha_hora) as rn
        from {{ ref('stg_tm_validaciones') }}
    )
    where rn > 1
),
tm_futuras as (
    select
        'TRANSMETRO' as fuente,
        cast(validacion_id as varchar) as id_registro,
        'fecha_futura' as motivo,
        'fecha_hora posterior al momento de la carga' as detalle,
        fecha_hora as fecha_hora_evento
    from {{ ref('stg_tm_validaciones') }}
    where fecha_hora > current_timestamp
),
tu_parada_nula as (
    select
        'TRANSURBANO' as fuente,
        cast(transaccion_id as varchar) as id_registro,
        'parada_nula' as motivo,
        'cod_parada vacio: no se puede atribuir a una zona' as detalle,
        fecha_hora as fecha_hora_evento
    from {{ ref('stg_tu_transacciones') }}
    where cod_parada is null
),
tu_futuras as (
    select
        'TRANSURBANO' as fuente,
        cast(transaccion_id as varchar) as id_registro,
        'fecha_futura' as motivo,
        'fecha posterior al momento de la carga (reloj de unidad desconfigurado)' as detalle,
        fecha_hora as fecha_hora_evento
    from {{ ref('stg_tu_transacciones') }}
    where fecha_hora > current_timestamp
),
mr_sin_salida as (
    select
        'METRORIEL' as fuente,
        cast(viaje_id as varchar) as id_registro,
        'viaje_sin_salida' as motivo,
        'el pasajero no valido salida: viaje no se puede cerrar' as detalle,
        ts_entrada as fecha_hora_evento
    from {{ ref('stg_mr_viajes') }}
    where sin_salida
),
tu_no_exitosas as (
    -- No es un defecto del dato (el registro esta bien formado), es una
    -- decision de negocio: una transaccion rechazada por el validador no
    -- es un abordaje. Se cuenta aqui para que nunca se pierda en silencio.
    select
        'TRANSURBANO' as fuente,
        cast(transaccion_id as varchar) as id_registro,
        'transaccion_no_exitosa' as motivo,
        'estado ' || estado_desc || ': intento de abordaje rechazado por el validador' as detalle,
        fecha_hora as fecha_hora_evento
    from {{ ref('stg_tu_transacciones') }}
    where estado_desc != 'OK'
      and cod_parada is not null
      and fecha_hora <= current_timestamp
)
select * from tm_duplicados
union all select * from tm_futuras
union all select * from tu_parada_nula
union all select * from tu_futuras
union all select * from mr_sin_salida
union all select * from tu_no_exitosas
