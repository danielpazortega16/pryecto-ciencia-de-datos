-- Tabla de features para ciencia de datos (2.3). Sale de Silver, no de Gold:
-- Gold ya agrego a un grano de negocio y aqui hace falta el evento atomico.
-- Entidad: una persona (persona_key, el mismo supuesto declarado en
-- dim_usuario: el numero dentro de la tarjeta vincula TM/TU/MR; Aerometro
-- queda como persona propia). Una fila por persona.
-- Fecha de corte: el dia siguiente al ultimo evento observado. Las ventanas
-- de 7/30/90 dias se cuentan hacia atras desde esa fecha, y solo se usan
-- eventos anteriores a ella.
with eventos as (
    select 'TRANSMETRO' as operador,
           {{ pseudonimo("'PERSONA'", "cast(cast(regexp_extract(tarjeta_tm, '[0-9]+') as bigint) as varchar)") }} as persona_key,
           fecha_hora, monto_gtq, zona_canonica as zona
    from {{ ref('silver_tm_validaciones') }}
    union all
    select 'TRANSURBANO',
           {{ pseudonimo("'PERSONA'", "cast(cast(regexp_extract(tarjeta_tu, '[0-9]+') as bigint) as varchar)") }},
           fecha_hora, monto_gtq, zona_canonica
    from {{ ref('silver_tu_transacciones') }}
    union all
    select 'METRORIEL',
           {{ pseudonimo("'PERSONA'", "cast(cast(regexp_extract(tarjeta_mr, '[0-9]+') as bigint) as varchar)") }},
           ts_entrada, monto_gtq, zona_entrada
    from {{ ref('silver_mr_viajes') }}
    union all
    select 'AEROMETRO',
           {{ pseudonimo("'AEROMETRO'", 'tarjeta_am') }},
           fecha_hora, monto_gtq, zona_canonica
    from {{ ref('silver_am_boardings') }}
),
corte as (
    select cast(max(fecha_hora) as date) + 1 as fecha_corte from eventos
)
select
    e.persona_key,
    c.fecha_corte,
    count(*) filter (where e.fecha_hora >= c.fecha_corte - 7)  as viajes_7d,
    count(*) filter (where e.fecha_hora >= c.fecha_corte - 30) as viajes_30d,
    count(*) filter (where e.fecha_hora >= c.fecha_corte - 90) as viajes_90d,
    count(*) as viajes_total,
    date_diff('day', cast(max(e.fecha_hora) as date), c.fecha_corte) as dias_desde_ultimo_viaje,
    count(distinct cast(e.fecha_hora as date)) as dias_activos,
    count(distinct e.operador) as n_modos_distintos,
    mode(e.operador) as modo_mas_usado,
    avg(case when {{ es_hora_pico('e.fecha_hora') }} then 1.0 else 0.0 end) as prop_hora_pico,
    avg(case when dayofweek(e.fecha_hora) in (0, 6) then 1.0 else 0.0 end) as prop_fin_de_semana,
    mode(e.zona) as zona_origen_mas_frecuente,
    sum(e.monto_gtq) as gasto_total_gtq,
    avg(e.monto_gtq) as gasto_promedio_gtq
from eventos e
cross join corte c
where e.fecha_hora < c.fecha_corte
group by e.persona_key, c.fecha_corte
