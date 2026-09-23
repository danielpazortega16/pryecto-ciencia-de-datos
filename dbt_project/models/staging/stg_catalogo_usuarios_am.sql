-- Aerometro no entrega padron. Catalogo minimo: solo la llave distinta
-- (el user_hash que el propio operador ya entrega seudonimizado).
select distinct tarjeta_am
from {{ ref('stg_am_boardings') }}
where tarjeta_am is not null
