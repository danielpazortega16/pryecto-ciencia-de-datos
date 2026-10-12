-- Demanda por modo, zona y hora (2.1). Una fila por fecha/hora/operador/zona.
select
    t.fecha,
    t.hora_del_dia,
    t.dia_habil,
    t.hora_pico,
    o.operador,
    o.nombre as operador_nombre,
    o.modo,
    z.zona_nombre,
    z.zona_tipo,
    count(*) as abordajes,
    sum(f.monto_gtq) as recaudo_gtq
from {{ ref('fact_abordaje') }} f
join {{ ref('dim_estacion') }} e on e.estacion_key = f.estacion_key
join {{ ref('dim_zona') }} z on z.zona_key = e.zona_key
join {{ ref('dim_tiempo') }} t on t.tiempo_key = f.tiempo_key
join {{ ref('dim_operador') }} o on o.operador = f.operador
group by 1, 2, 3, 4, 5, 6, 7, 8, 9
