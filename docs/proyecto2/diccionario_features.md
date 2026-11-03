# Diccionario de features

Todas se calculan por unidad (persona) y fecha de corte t, con la ventana
[t - 28 días, t). Las cuatro tablas de abordajes de Silver son
silver_tm_validaciones, silver_tu_transacciones, silver_mr_viajes (se toma la
entrada del viaje) y silver_am_boardings; en adelante "abordajes de Silver".
Solo tienen registros válidos: lo que está en cuarentena no llega a ellas.
Ninguna ventana pasa de 28 días.

| Feature | Qué mide | Ventana | Tabla de Silver |
|---|---|---|---|
| viajes_28d | Abordajes válidos de la persona en las 4 semanas antes del corte | 28 días | abordajes de Silver |
| viajes_7d | Abordajes en los últimos 7 días antes del corte | 7 días | abordajes de Silver |
| viajes_14d | Abordajes en los últimos 14 días antes del corte | 14 días | abordajes de Silver |
| tendencia_14d | (viajes de los últimos 14 días + 1) / (viajes de los 14 días anteriores + 1); menor que 1 es caída | 28 días | abordajes de Silver |
| dias_activos_28d | Días distintos con al menos un abordaje | 28 días | abordajes de Silver |
| dias_desde_ultimo_viaje | Días (con decimales) entre el último abordaje y el corte | 28 días | abordajes de Silver |
| max_dias_sin_viajar | Hueco más largo, en días, entre dos días con viaje dentro de la ventana | 28 días | abordajes de Silver |
| viajes_por_dia_activo | viajes_28d / dias_activos_28d | 28 días | abordajes de Silver |
| n_operadores | Operadores distintos que usó | 28 días | abordajes de Silver |
| n_zonas | Zonas distintas donde abordó | 28 días | abordajes de Silver |
| prop_transmetro | Proporción de sus abordajes en Transmetro | 28 días | silver_tm_validaciones sobre el total |
| prop_transurbano | Proporción en Transurbano | 28 días | silver_tu_transacciones sobre el total |
| prop_metroriel | Proporción en MetroRiel | 28 días | silver_mr_viajes sobre el total |
| prop_aerometro | Proporción en Aerómetro | 28 días | silver_am_boardings sobre el total |
| prop_hora_pico | Proporción de abordajes entre 5:00 y 8:59 o entre 16:00 y 19:59 (misma definición que dim_tiempo) | 28 días | abordajes de Silver |
| prop_fin_de_semana | Proporción de abordajes en sábado o domingo | 28 días | abordajes de Silver |
| gasto_28d | Suma de tarifas pagadas, en quetzales | 28 días | abordajes de Silver |
| tarifa_promedio | Tarifa promedio por abordaje | 28 días | abordajes de Silver |
| perfil | Perfil del padrón vigente antes del corte (estudiante, trabajador, adulto_mayor, general); sin_padron si la persona no tiene alta en el CDC | eventos del CDC antes del corte | silver_cdc_padron |

Columnas que no son features: unidad_id, corte, fecha_corte, tarjetas (las
llaves originales de la persona vistas antes del corte, separadas por ";") y
etiqueta (vacía en el corte C).
