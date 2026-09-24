{% macro bronze_parquet(nombre) %}
read_parquet('{{ env_var("PROJECT_ROOT") }}/bronze/{{ nombre }}/**/*.parquet')
{% endmacro %}
