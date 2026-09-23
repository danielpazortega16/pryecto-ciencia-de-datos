-- Grano declarado: UN ABORDAJE -- un usuario accede a un modo en una
-- estacion/parada en un momento dado. Se eligio este grano (no "viaje
-- puerta a puerta") porque tres de los cuatro operadores solo registran
-- el acceso, no el cierre del viaje; ver docs/decisiones.md. Para
-- MetroRiel, que si cierra el viaje, se usa el evento de ENTRADA como el
-- abordaje (el viaje completo vive en fact_viaje_metroriel).
with tm as (
    select
        'TRANSMETRO' as operador,
        cast(validacion_id as varchar) as id_origen,
        'TRANSMETRO:' || tarjeta_tm as usuario_key,
        estacion_id as codigo_estacion,
        fecha_hora,
        monto_gtq,
        es_transbordo
    from {{ ref('silver_tm_validaciones') }}
),
tu as (
    select
        'TRANSURBANO' as operador,
        cast(transaccion_id as varchar) as id_origen,
        'TRANSURBANO:' || tarjeta_tu as usuario_key,
        cod_parada as codigo_estacion,
        fecha_hora,
        monto_gtq,
        false as es_transbordo
    from {{ ref('silver_tu_transacciones') }}
),
mr as (
    select
        'METRORIEL' as operador,
        cast(viaje_id as varchar) as id_origen,
        'METRORIEL:' || tarjeta_mr as usuario_key,
        cast(estacion_entrada as varchar) as codigo_estacion,
        ts_entrada as fecha_hora,
        monto_gtq,
        false as es_transbordo
    from {{ ref('silver_mr_viajes') }}
),
am as (
    select
        'AEROMETRO' as operador,
        cast(boarding_id as varchar) as id_origen,
        'AEROMETRO:' || tarjeta_am as usuario_key,
        station_code as codigo_estacion,
        fecha_hora,
        monto_gtq,
        false as es_transbordo
    from {{ ref('silver_am_boardings') }}
),
unido as (
    select * from tm union all select * from tu
    union all select * from mr union all select * from am
)
select
    u.operador || ':' || u.id_origen as abordaje_key,
    u.operador,
    u.usuario_key,
    e.estacion_key,
    cast(strftime(u.fecha_hora, '%Y%m%d%H') as bigint) as tiempo_key,
    u.fecha_hora,
    u.monto_gtq,
    u.es_transbordo
from unido u
left join {{ ref('dim_estacion') }} e
    on e.operador = u.operador and e.codigo_nativo = u.codigo_estacion
