-- Regla de calidad: duplicados de torniquete (mismo validacion_id repetido)
-- y fechas del futuro van a cuarentena (ver silver_cuarentena), no se
-- descartan en silencio.
with deduplicado as (
    select *, row_number() over (partition by validacion_id order by fecha_hora) as rn
    from {{ ref('stg_tm_validaciones') }}
)
select
    d.validacion_id,
    d.tarjeta_tm,
    d.estacion_id,
    d.linea,
    d.fecha_hora,
    d.monto_gtq,
    d.tipo,
    (d.tipo = 'TRANSBORDO') as es_transbordo,
    e.zona_canonica
from deduplicado d
left join {{ ref('stg_tm_estaciones') }} e on e.estacion_id = d.estacion_id
where d.rn = 1
  and d.fecha_hora <= current_timestamp
