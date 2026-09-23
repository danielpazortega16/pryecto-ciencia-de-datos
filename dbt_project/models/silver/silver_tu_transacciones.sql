-- Reglas de calidad: codigo de parada nulo y fecha del futuro van a
-- cuarentena. Ademas, una decision de negocio (no de calidad de dato):
-- solo las transacciones con estado_desc = 'OK' cuentan como abordaje
-- real; SALDO_INSUF/TARJETA_INVALIDA son intentos fallidos, no viajes.
select
    t.transaccion_id,
    t.tarjeta_tu,
    t.cod_parada,
    t.ruta,
    t.fecha_hora,
    t.monto_gtq,
    t.estado_desc,
    p.zona_canonica
from {{ ref('stg_tu_transacciones') }} t
left join {{ ref('silver_tu_paradas') }} p on p.cod_parada = t.cod_parada
where t.cod_parada is not null
  and t.fecha_hora <= current_timestamp
  and t.estado_desc = 'OK'
