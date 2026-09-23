-- DDL generado desde el catalogo de DuckDB (capa Gold)

CREATE TABLE main_gold.dim_estacion (
    estacion_key BIGINT,
    operador VARCHAR,
    codigo_nativo VARCHAR,
    nombre VARCHAR,
    zona_key BIGINT,
    lat DOUBLE,
    lon DOUBLE
);

CREATE TABLE main_gold.dim_operador (
    operador VARCHAR,
    nombre VARCHAR,
    modo VARCHAR,
    unidades_infra INTEGER
);

CREATE TABLE main_gold.dim_tiempo (
    tiempo_key BIGINT,
    fecha DATE,
    hora_del_dia BIGINT,
    dia_habil BOOLEAN,
    hora_pico BOOLEAN
);

CREATE TABLE main_gold.dim_usuario (
    usuario_key VARCHAR,
    operador VARCHAR,
    llave_nativa VARCHAR,
    perfil VARCHAR,
    zona_residencia VARCHAR,
    estado_padron VARCHAR
);

CREATE TABLE main_gold.dim_zona (
    zona_key BIGINT,
    zona_nombre VARCHAR,
    zona_tipo VARCHAR
);

CREATE TABLE main_gold.fact_abordaje (
    abordaje_key VARCHAR,
    operador VARCHAR,
    usuario_key VARCHAR,
    estacion_key BIGINT,
    tiempo_key BIGINT,
    fecha_hora TIMESTAMP,
    monto_gtq DOUBLE,
    es_transbordo BOOLEAN
);

CREATE TABLE main_gold.fact_viaje_metroriel (
    viaje_id BIGINT,
    usuario_key VARCHAR,
    estacion_origen_key BIGINT,
    estacion_destino_key BIGINT,
    tiempo_key_entrada BIGINT,
    ts_entrada TIMESTAMP,
    ts_salida TIMESTAMP,
    duracion_s INTEGER,
    monto_gtq DOUBLE
);
