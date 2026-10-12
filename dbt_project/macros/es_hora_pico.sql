{% macro es_hora_pico(columna_ts) %}
extract(hour from {{ columna_ts }}) in (5, 6, 7, 8, 16, 17, 18, 19)
{% endmacro %}
