select
    cast(validacion_id as bigint) as validacion_id,
    tarjeta as tarjeta_tm,
    estacion_id,
    linea,
    strptime(fecha_hora, '%Y-%m-%d %H:%M:%S') as fecha_hora,
    cast(tarifa as double) as monto_gtq,
    tipo,
    ts_ingesta
from {{ source('bronze', 'tm_validaciones') }}
