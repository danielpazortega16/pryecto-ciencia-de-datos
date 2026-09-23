-- Grano: una hora. Cubre el rango real observado en los datos limpios de
-- Silver, no un calendario fijo, para que dim_tiempo crezca con los datos.
with rango as (
    select min(fecha_hora) as min_ts, max(fecha_hora) as max_ts
    from (
        select fecha_hora from {{ ref('silver_tm_validaciones') }}
        union all select fecha_hora from {{ ref('silver_tu_transacciones') }}
        union all select ts_entrada as fecha_hora from {{ ref('silver_mr_viajes') }}
        union all select fecha_hora from {{ ref('silver_am_boardings') }}
    )
),
horas as (
    select unnest(generate_series(
        date_trunc('hour', min_ts),
        date_trunc('hour', max_ts),
        interval '1 hour'
    )) as hora_ts
    from rango
)
select
    cast(strftime(hora_ts, '%Y%m%d%H') as bigint) as tiempo_key,
    cast(hora_ts as date) as fecha,
    extract(hour from hora_ts) as hora_del_dia,
    dayofweek(hora_ts) not in (0, 6) as dia_habil,
    extract(hour from hora_ts) in (5, 6, 7, 8, 16, 17, 18, 19) as hora_pico
from horas
