-- Origen-destino de MetroRiel por estacion (viajes completos).
select
    eo.codigo_nativo as estacion_origen,
    zo.zona_nombre as zona_origen,
    ed.codigo_nativo as estacion_destino,
    zd.zona_nombre as zona_destino,
    count(*) as viajes,
    avg(v.duracion_s) as duracion_promedio_s
from {{ ref('fact_viaje_metroriel') }} v
join {{ ref('dim_estacion') }} eo on eo.estacion_key = v.estacion_origen_key
join {{ ref('dim_zona') }} zo on zo.zona_key = eo.zona_key
join {{ ref('dim_estacion') }} ed on ed.estacion_key = v.estacion_destino_key
join {{ ref('dim_zona') }} zd on zd.zona_key = ed.zona_key
group by 1, 2, 3, 4
