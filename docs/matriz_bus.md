# Matriz del bus de procesos

fact_abordaje (grano: un abordaje a cualquier modo) usa las cuatro
dimensiones conformadas: tiempo, zona a través de la estación, estación,
usuario y operador.

fact_viaje_metroriel (grano: un viaje completo puerta a puerta) usa
tiempo, zona a través de las estaciones de origen y destino, estación
tanto de origen como de destino, y usuario. El operador es implícito,
siempre es MetroRiel.

Las dos tablas comparten tiempo, zona, estación y usuario, que son las
dimensiones conformadas de la Agencia. Por eso se puede cruzar cualquier
pregunta que compare "abordajes en general" contra "viajes completos de
MetroRiel", por ejemplo ver la demanda total en una zona contra los
viajes de MetroRiel que realmente la atienden, sin tener que reconciliar
nada entre las dos tablas.
