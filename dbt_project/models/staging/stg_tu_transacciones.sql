select
    row_number() over (order by fecha, hora, num_tarjeta) as transaccion_id,  -- Transurbano no trae PK propia
    num_tarjeta as tarjeta_tu,
    nullif(cod_parada, '') as cod_parada,
    ruta,
    -- fecha viene DD/MM/YYYY, hora en columna separada: se unen a un solo timestamp
    strptime(fecha || ' ' || hora, '%d/%m/%Y %H:%M:%S') as fecha_hora,
    cast(monto_centavos as double) / 100.0 as monto_gtq,
    cast(cod_estado as integer) as cod_estado,
    case cast(cod_estado as integer)
        when 1 then 'OK' when 2 then 'OK' when 3 then 'OK'
        when 7 then 'SALDO_INSUF' when 9 then 'TARJETA_INVALIDA'
        else 'DESCONOCIDO'
    end as estado_desc
from {{ bronze_parquet('tu_transacciones') }}
