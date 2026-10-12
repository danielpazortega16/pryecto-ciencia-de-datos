# Definiciones oficiales y dueños

Los cuatro operadores cuentan distinto. Estas son las definiciones que
usa la Agencia y que respetan el tablero, la tabla de features y
cualquier consulta sobre Gold. Si dos personas del equipo calculan
"viajes del mes" con la consulta de abajo, obtienen el mismo número.

## Qué cuenta como un viaje

Un viaje es un abordaje válido: un acceso a un modo, aceptado por el
validador, que pasó las reglas de calidad de Silver (sin duplicado de
torniquete, con código de parada, con fecha no futura y, en Transurbano,
con estado OK). Es la fila de fact_abordaje.

Un trayecto que combina varios modos cuenta como varios viajes, uno por
cada abordaje. Esto es deliberado: tres de los cuatro operadores no
registran dónde se baja el pasajero, así que no se puede reconstruir el
trayecto completo sin inventar datos.

MetroRiel además tiene "viaje completo" (fact_viaje_metroriel), que exige
entrada y salida. Un viaje completo se mide siempre con ese nombre y
nunca se suma con los abordajes de otros operadores.

Los intentos rechazados por el validador (Transurbano con saldo
insuficiente o tarjeta inválida) no son viajes. Quedan en
silver_cuarentena con el motivo transaccion_no_exitosa.

Consulta oficial de viajes del mes (junio de 2026 da 1,093,235):

```sql
select count(*) from main_gold.fact_abordaje
where fecha_hora >= date '2026-06-01' and fecha_hora < date '2026-07-01';
```

## Qué cuenta como un usuario activo

Un usuario activo es una persona (persona_key) con al menos un abordaje
en los 30 días anteriores a la fecha de corte. A la fecha de corte
actual (16 de julio de 2026) hay 70,332 personas activas de 70,380.

```sql
select count(*) from main_features.feat_usuario where viajes_30d > 0;
```

Una persona se identifica con el supuesto declarado en
docs/decisiones.md: el número dentro de la tarjeta vincula Transmetro,
Transurbano y MetroRiel, y Aerómetro cuenta como persona aparte. Por eso
la cifra de usuarios activos es una aproximación. Tampoco se descuentan
las tarjetas dadas de baja en el padrón de Transmetro, porque la baja
solo se conoce para las tarjetas que tuvieron alta en el CDC.

## Otras definiciones

Hora pico: de 5:00 a 8:59 y de 16:00 a 19:59. Sale de la distribución de
abordajes observada y está implementada una sola vez, en el macro
es_hora_pico de dbt, que usan dim_tiempo y la tabla de features.

Día hábil: lunes a viernes. No se descuentan feriados.

Zona: la que figura en el catálogo de estaciones del operador, ya
conformada a "Zona N" o nombre de municipio. Un abordaje pertenece a la
zona de la estación o parada donde ocurrió, nunca a la zona del usuario.

Recaudo: suma de monto_gtq de los abordajes válidos, en quetzales.

## Dueño por dominio

| Dominio | Responde por él | Quién autoriza un cambio |
|---|---|---|
| Zona (dim_zona) | Coordinación de datos de la Agencia | La Agencia, previa consulta con la Municipalidad, que es quien define las zonas oficiales |
| Estación y parada (dim_estacion) | Cada operador por sus propios códigos; la Agencia por la conformación | El operador propone, la Agencia aprueba |
| Tiempo, hora pico y día hábil (dim_tiempo) | Coordinación de datos de la Agencia | La dirección de la Agencia, porque cambia los resultados históricos |
| Usuario y persona (dim_usuario) | Coordinación de datos junto con seguridad de la información | Seguridad de la información, porque toca datos personales |
| Definición de viaje y usuario activo | Dirección de la Agencia | La dirección de la Agencia, comunicada a los cuatro operadores |
| Reglas de calidad y cuarentena | Coordinación de datos | Coordinación de datos, avisando a los operadores afectados |

Si mañana cambia la definición de zona, por ejemplo porque la
Municipalidad redefine un límite, la aprueba la Agencia, se actualiza el
catálogo, se vuelve a correr el pipeline completo y se avisa a los
operadores, porque los números históricos por zona cambian.
