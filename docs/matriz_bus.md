# Matriz del bus de procesos

| Proceso de negocio | dim_tiempo | dim_zona | dim_estacion | dim_usuario | dim_operador |
|---|---|---|---|---|---|
| Abordaje a cualquier modo (`fact_abordaje`) | X | X (vía estación) | X | X | X |
| Viaje completo en MetroRiel (`fact_viaje_metroriel`) | X | X (vía estación origen/destino) | X (origen y destino) | X | — (implícito, siempre MetroRiel) |

Ambos procesos comparten `dim_tiempo`, `dim_zona`, `dim_estacion` y
`dim_usuario`: son las dimensiones conformadas de la Agencia. Cualquier
pregunta que cruce "abordajes en general" con "viajes completos de
MetroRiel" (por ejemplo, comparar demanda total en una zona contra los
viajes MetroRiel que realmente la atienden) es válida porque ambas tablas
de hechos apuntan a las mismas dimensiones.
