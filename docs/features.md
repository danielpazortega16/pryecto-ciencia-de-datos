# Tabla de features para ciencia de datos

La tabla es main_features.feat_usuario, construida en
dbt_project/models/features/feat_usuario.sql. Se arma a partir de las
tablas de Silver, no de Gold: Gold ya agregó a un grano de negocio y aquí
hace falta el evento atómico para agregarlo de otra manera.

La entidad es una persona (persona_key), una fila por persona, con 70,380
filas. Usa el mismo supuesto de identidad que dim_usuario: el número
dentro de la tarjeta vincula Transmetro, Transurbano y MetroRiel, y
Aerómetro cuenta como persona aparte.

Fecha de corte declarada: 16 de julio de 2026 (el día siguiente al último
evento observado). Solo se usan eventos anteriores a esa fecha y las
ventanas se cuentan hacia atrás desde ella. Como los datos cubren 45 días,
la ventana de 90 días abarca todo el periodo y da lo mismo que el total.

| Columna | Qué es |
|---|---|
| persona_key | Seudónimo de la persona |
| fecha_corte | Fecha de corte, igual en todas las filas |
| viajes_7d, viajes_30d, viajes_90d | Abordajes en los últimos 7, 30 y 90 días antes del corte |
| viajes_total | Abordajes en todo el periodo observado |
| dias_desde_ultimo_viaje | Días entre su último abordaje y la fecha de corte |
| dias_activos | Días distintos con al menos un abordaje |
| n_modos_distintos | Cantidad de operadores distintos que usó |
| modo_mas_usado | Operador con más abordajes (en empate, el que elija DuckDB) |
| prop_hora_pico | Proporción de sus abordajes en hora pico |
| prop_fin_de_semana | Proporción de sus abordajes en sábado o domingo |
| zona_origen_mas_frecuente | Zona donde más aborda |
| gasto_total_gtq | Suma de tarifas en quetzales |
| gasto_promedio_gtq | Tarifa promedio por abordaje |

Con esta tabla se podría predecir qué personas dejarán de usar el
sistema en los próximos 30 días, lo que le serviría a la Agencia para
dirigir campañas de retención y detectar a tiempo las zonas donde la
demanda empieza a caer. La tabla no trae la variable a predecir; para
entrenar habría que calcularla con datos posteriores a la fecha de corte.
