-- Conforma la dimension zona para Transurbano: "Z10" -> "Zona 10",
-- "VILLA NUEVA" -> "Villa Nueva" (mismo criterio que usan Transmetro,
-- MetroRiel y Aerometro, que ya llegan canonicos).
select
    cod_parada,
    descripcion,
    ruta,
    case
        when es_zona_numerada then 'Zona ' || regexp_extract(sector_crudo, '[0-9]+')
        else array_to_string(
                list_transform(
                    string_split(lower(sector_crudo), ' '),
                    w -> upper(substr(w, 1, 1)) || substr(w, 2)
                ),
                ' '
             )
    end as zona_canonica
from {{ ref('stg_tu_paradas') }}
