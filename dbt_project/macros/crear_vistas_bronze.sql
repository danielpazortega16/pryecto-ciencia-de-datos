{% macro crear_vistas_bronze() %}
    {% if execute %}
        {% set fuentes = ['tm_estaciones', 'tu_paradas', 'mr_estaciones', 'am_estaciones',
                          'mr_viajes', 'tm_validaciones', 'am_boardings',
                          'tu_transacciones', 'cdc_padron_usuarios'] %}
        {% do run_query("create schema if not exists bronze") %}
        {% for f in fuentes %}
            {% do run_query("create or replace view bronze." ~ f ~ " as select * from read_parquet('" ~ env_var('PROJECT_ROOT') ~ "/bronze/" ~ f ~ "/**/*.parquet')") %}
        {% endfor %}
    {% endif %}
{% endmacro %}
