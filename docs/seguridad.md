# Seguridad y manejo de datos personales

Los datos del proyecto son generados, pero un sistema real de transporte
sabe dónde estuvo cada persona y a qué hora, todos los días. Se tomaron
cuatro decisiones.

## Credenciales

No hay credenciales en el repositorio. El pipeline no necesita
contraseñas: DuckDB es un archivo local y Prefect corre sin servidor. Lo
único sensible es la sal con que se seudonimiza la tarjeta, y esa se lee
de la variable de entorno PSEUDO_SALT. El archivo .env.example muestra el
nombre de la variable sin valor, y .env está en .gitignore. Si la
variable no existe se usa una sal de desarrollo, que sirve para probar
pero no protege nada; en una puesta en producción la sal es obligatoria,
distinta por ambiente y guardada en un gestor de secretos.

## Seudonimización

La tarjeta en claro no pasa a Gold. Antes de construir dim_usuario y las
tablas de hechos, la llave se convierte en usuario_key con sha256 de la
sal, el operador y la tarjeta, y se conservan 16 caracteres. El tablero
no necesita saber qué tarjeta es, solo que es la misma persona: con el
seudónimo se puede contar viajes por usuario, medir transbordo y
construir features. Los archivos que lee Tableau son tablas resumen sin
ninguna llave de usuario.

El límite honesto: la tarjeta en claro sigue existiendo en Bronze y en
Silver, y por lo tanto dentro de warehouse.duckdb. Esas capas son de
acceso restringido (ver abajo). Además, sin sal secreta un hash de una
tarjeta de 8 dígitos se puede deshacer probando todas las combinaciones,
por eso la sal no se sube al repositorio y debe cambiarse si se filtra.

## Quién ve qué

El analista de la Agencia ve solo las tablas resumen y Gold, nunca el
detalle por individuo. El científico de datos ve Gold y la tabla de
features, que están seudonimizadas. El auditor de fraude puede pedir
acceso a Silver, donde está la tarjeta en claro, solo con autorización de
seguridad de la información y dejando bitácora de cada consulta.
Ingeniería de datos accede a Bronze para operar el pipeline y no lo usa
para análisis. Los operadores ven únicamente sus propios datos.

## Retención

El detalle individual (Bronze y Silver, con la tarjeta en claro) se
conserva 13 meses: un año completo para poder comparar estaciones del año
más un mes para cerrar conciliaciones y reclamos de tarifa, que es el
motivo por el que alguien necesita volver a un viaje concreto. Pasado ese
plazo el detalle se borra o se reemplaza por su seudónimo. Los datos
seudonimizados de Gold se conservan 24 meses para análisis de tendencia,
y las tablas resumen sin llaves de usuario no tienen plazo, porque ya no
identifican a nadie. Los plazos son una propuesta del equipo y deben
confirmarse con el área legal de la Agencia.
