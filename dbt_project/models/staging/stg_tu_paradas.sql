select
    cod_parada,
    descripcion,
    ruta,
    sector as sector_crudo,
    -- Transurbano guarda la zona como "Z10" (Zona N) o el municipio en
    -- MAYUSCULAS sin prefijo (ej. "VILLA NUEVA"). Se conforma en Silver,
    -- aqui solo se separa el patron para que Silver no repita el regex.
    regexp_matches(sector, '^Z[0-9]+$') as es_zona_numerada
from {{ source('bronze', 'tu_paradas') }}
