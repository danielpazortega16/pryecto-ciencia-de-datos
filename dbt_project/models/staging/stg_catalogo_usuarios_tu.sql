-- Transurbano no entrega padron. Catalogo minimo: solo la llave distinta
-- que aparece en su archivo de operacion. Sin nombre, sin fecha de alta,
-- sin atributos: no se inventan datos que el operador nunca entrego.
select distinct tarjeta_tu
from {{ ref('stg_tu_transacciones') }}
where tarjeta_tu is not null
