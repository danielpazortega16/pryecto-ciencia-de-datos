# Diagrama del modelo de Gold

Hay dos tablas de hechos y cinco dimensiones. Las dimensiones se comparten
entre las dos tablas de hechos, y por eso se pueden cruzar sin reconciliar
nada (ver docs/matriz_bus.md).

```mermaid
erDiagram
    dim_zona ||--o{ dim_estacion : "zona de la estacion"
    dim_operador ||--o{ fact_abordaje : "modo"
    dim_estacion ||--o{ fact_abordaje : "donde aborda"
    dim_tiempo ||--o{ fact_abordaje : "cuando"
    dim_usuario ||--o{ fact_abordaje : "quien"
    dim_estacion ||--o{ fact_viaje_metroriel : "estacion de origen"
    dim_estacion ||--o{ fact_viaje_metroriel : "estacion de destino"
    dim_tiempo ||--o{ fact_viaje_metroriel : "hora de entrada"
    dim_usuario ||--o{ fact_viaje_metroriel : "quien"

    fact_abordaje {
        varchar abordaje_key PK
        varchar operador FK
        varchar usuario_key FK
        bigint estacion_key FK
        bigint tiempo_key FK
        timestamp fecha_hora
        double monto_gtq
        boolean es_transbordo
    }

    fact_viaje_metroriel {
        bigint viaje_id PK
        varchar usuario_key FK
        bigint estacion_origen_key FK
        bigint estacion_destino_key FK
        bigint tiempo_key_entrada FK
        timestamp ts_entrada
        timestamp ts_salida
        integer duracion_s
        double monto_gtq
    }

    dim_zona {
        bigint zona_key PK
        varchar zona_nombre
        varchar zona_tipo
    }

    dim_estacion {
        bigint estacion_key PK
        varchar operador
        varchar codigo_nativo
        varchar nombre
        bigint zona_key FK
        double lat
        double lon
    }

    dim_tiempo {
        bigint tiempo_key PK
        date fecha
        bigint hora_del_dia
        boolean dia_habil
        boolean hora_pico
    }

    dim_usuario {
        varchar usuario_key PK
        varchar operador
        varchar perfil
        varchar zona_residencia
        varchar estado_padron
        varchar persona_key
        varchar vinculo_persona
    }

    dim_operador {
        varchar operador PK
        varchar nombre
        varchar modo
        integer unidades_infra
    }
```

## Cómo leerlo

fact_abordaje es la tabla principal. Cada fila es un abordaje: una persona que
entra a un modo, en una estación o parada, a una hora. Entran los cuatro
operadores, y de MetroRiel se toma la entrada del viaje.

fact_viaje_metroriel es la segunda y solo existe para MetroRiel. Cada fila es
un viaje completo, con estación de entrada y de salida. Apunta dos veces a
dim_estacion, una por el origen y otra por el destino.

La zona de un abordaje no está en la tabla de hechos sino en la estación:
fact_abordaje llega a dim_zona pasando por dim_estacion.

usuario_key es un seudónimo de la tarjeta de un operador. persona_key, que
vive en dim_usuario, agrupa tarjetas bajo el supuesto que se explica en
docs/decisiones.md.

## Medidas

monto_gtq es aditiva: se puede sumar por zona, hora, operador o lo que sea.
El conteo de abordajes o de viajes también. duracion_s no es aditiva, solo se
promedia. es_transbordo es una marca y se cuenta, no se suma.

## Dimensiones que sirven a las dos tablas

dim_tiempo, dim_estacion y dim_usuario las usan los dos hechos. dim_zona se
llega desde dim_estacion. dim_operador la usa solo fact_abordaje porque el
operador de fact_viaje_metroriel siempre es MetroRiel.
