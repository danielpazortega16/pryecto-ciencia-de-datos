# Tablero en Tableau

El archivo es tableau/tablero_agencia.twbx (libro empaquetado, trae los datos
dentro). Se abre con Tableau Public o Tableau Desktop y la pestaña "Tablero
de la Agencia" reúne las seis hojas. Cada hoja usa una de las tablas resumen
de la capa Gold exportadas a CSV en la misma carpeta (mart_demanda,
mart_cobertura_zona, mart_transbordo, mart_metroriel_zona y
mart_metroriel_od), así que de cada número del tablero se llega a una tabla
de Gold y de ahí, por docs/linaje.md, hasta el archivo crudo.

Si se regeneran los datos, python orquestacion/flow_prefect.py vuelve a
escribir los CSV y en Tableau basta con actualizar los orígenes de datos.

## Qué responde cada hoja

Demanda por hora y modo: líneas de abordajes por hora del día, una por
operador. Todos los modos tienen dos picos, a las 7:00 (197,491 abordajes
sumando los cuatro) y a las 17:00. Es la hoja que responde cuándo se
concentra la demanda.

Demanda por zona y modo: barras apiladas por zona, coloreadas por operador.
Las cinco zonas de MetroRiel (17, 12, 8, 6 y 1) son las cinco de mayor
demanda, entre 137,170 y 148,554 abordajes cada una. Responde dónde se
concentra.

Cobertura por zona: cantidad de modos que sirven cada zona, de las 25 zonas
de la ciudad más los municipios. Trece zonas aparecen en cero, sin ningún
operador. Las zonas 1, 12 y 17 son las únicas con los cuatro.

Transbordo entre sistemas: personas según la combinación de operadores que
usan. 36,827 de 70,380 usan más de uno, bajo el supuesto de vinculación por
número de tarjeta que se explica en docs/decisiones.md. No es una medición
directa y Aerómetro queda subestimado.

Caso MetroRiel por zona: para cada zona, abordajes de los otros tres modos
contra abordajes de MetroRiel. En naranja están las zonas del trazado. Las
tres zonas sin MetroRiel con más demanda de otros modos son Mixco, Zona 7 y
Zona 13.

MetroRiel origen y destino: matriz de viajes completos entre zonas de las
estaciones de MetroRiel (295,511 viajes). Solo el 16.5% de los viajes
empieza y termina en la misma zona.

La recomendación que sale de estas hojas está en docs/recomendacion.md.
