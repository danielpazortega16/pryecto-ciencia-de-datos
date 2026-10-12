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
    perfil VARCHAR,
    zona_residencia VARCHAR,
    estado_padron VARCHAR,
    persona_key VARCHAR,
    vinculo_persona VARCHAR
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

CREATE TABLE main_gold.mart_cobertura_zona (
    zona_nombre VARCHAR,
    zona_tipo VARCHAR,
    estaciones_transmetro BIGINT,
    paradas_transurbano BIGINT,
    estaciones_metroriel BIGINT,
    estaciones_aerometro BIGINT,
    n_modos_con_servicio INTEGER,
    abordajes_total HUGEINT
);

CREATE TABLE main_gold.mart_demanda (
    fecha DATE,
    hora_del_dia BIGINT,
    dia_habil BOOLEAN,
    hora_pico BOOLEAN,
    operador VARCHAR,
    operador_nombre VARCHAR,
    modo VARCHAR,
    zona_nombre VARCHAR,
    zona_tipo VARCHAR,
    abordajes BIGINT,
    recaudo_gtq DOUBLE
);

CREATE TABLE main_gold.mart_metroriel_od (
    estacion_origen VARCHAR,
    zona_origen VARCHAR,
    estacion_destino VARCHAR,
    zona_destino VARCHAR,
    viajes BIGINT,
    duracion_promedio_s DOUBLE
);

CREATE TABLE main_gold.mart_metroriel_zona (
    zona_nombre VARCHAR,
    zona_tipo VARCHAR,
    estaciones_metroriel BIGINT,
    en_trazado_metroriel BOOLEAN,
    abordajes_otros_modos HUGEINT,
    abordajes_metroriel HUGEINT,
    ranking_demanda_otros_modos BIGINT
);

CREATE TABLE main_gold.mart_transbordo (
    n_operadores BIGINT,
    combinacion VARCHAR,
    personas BIGINT
);
