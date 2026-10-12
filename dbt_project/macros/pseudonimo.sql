{% macro pseudonimo(operador, llave) %}
substr(sha256('{{ env_var("PSEUDO_SALT", "salt-de-desarrollo-cambiar") }}' || ':' || {{ operador }} || ':' || {{ llave }}), 1, 16)
{% endmacro %}
