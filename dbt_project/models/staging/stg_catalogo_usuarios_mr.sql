-- MetroRiel no entrega padron. Catalogo minimo: solo la llave distinta.
select distinct tarjeta_mr
from {{ ref('stg_mr_viajes') }}
where tarjeta_mr is not null
