{% macro ultima_carga(fuente) %}
(
    select * from {{ source('bronze', fuente) }}
    where fecha_ingesta = (select max(fecha_ingesta) from {{ source('bronze', fuente) }})
)
{% endmacro %}
