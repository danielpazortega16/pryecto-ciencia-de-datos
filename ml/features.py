"""Poblacion, features y etiqueta para una fecha de corte.

Todo sale de la capa Silver (solo registros validos: lo que esta en
cuarentena no esta en esas tablas). La unidad es la persona: el numero
dentro de la tarjeta vincula Transmetro, Transurbano y MetroRiel (mismo
supuesto que dim_usuario del Proyecto 1) y Aerometro queda como persona
aparte porque entrega un hash que no se puede vincular.

Regla del corte t (00:00 hora local):
  features  -> eventos en [t - 28 dias, t)
  etiqueta  -> 1 si no hay ningun abordaje valido en [t, t + 30 dias)
  poblacion -> al menos 2 abordajes validos en la ventana de features y
               sin un DELETE del CDC vigente antes de t

El parametro datos_hasta recorta los datos de entrada (eventos y CDC) antes
de calcular; lo usa la prueba de recorte para demostrar que las features no
dependen de nada posterior al corte.
"""
from datetime import date, datetime, timedelta

import duckdb
import pandas as pd

from ml.config import DB_PATH, HORIZONTE_DIAS, MIN_VIAJES_POBLACION, VENTANA_DIAS

COLUMNAS_NUMERICAS = [
    "viajes_28d",
    "viajes_7d",
    "viajes_14d",
    "tendencia_14d",
    "dias_activos_28d",
    "dias_desde_ultimo_viaje",
    "max_dias_sin_viajar",
    "viajes_por_dia_activo",
    "n_operadores",
    "n_tarjetas",
    "n_zonas",
    "prop_transmetro",
    "prop_transurbano",
    "prop_metroriel",
    "prop_aerometro",
    "prop_hora_pico",
    "prop_fin_de_semana",
    "gasto_28d",
    "tarifa_promedio",
]
COLUMNAS_CATEGORICAS = ["perfil"]
COLUMNAS_FEATURES = COLUMNAS_NUMERICAS + COLUMNAS_CATEGORICAS

_EVENTOS_SQL = """
    select 'P' || cast(cast(regexp_extract(tarjeta_tm, '[0-9]+') as bigint) as varchar) as unidad_id,
           cast(regexp_extract(tarjeta_tm, '[0-9]+') as bigint) as numero,
           tarjeta_tm as tarjeta, 'TRANSMETRO' as operador, fecha_hora, monto_gtq,
           zona_canonica as zona
    from main_silver.silver_tm_validaciones
    union all
    select 'P' || cast(cast(regexp_extract(tarjeta_tu, '[0-9]+') as bigint) as varchar),
           cast(regexp_extract(tarjeta_tu, '[0-9]+') as bigint),
           tarjeta_tu, 'TRANSURBANO', fecha_hora, monto_gtq, zona_canonica
    from main_silver.silver_tu_transacciones
    union all
    select 'P' || cast(cast(regexp_extract(tarjeta_mr, '[0-9]+') as bigint) as varchar),
           cast(regexp_extract(tarjeta_mr, '[0-9]+') as bigint),
           tarjeta_mr, 'METRORIEL', ts_entrada, monto_gtq, zona_entrada
    from main_silver.silver_mr_viajes
    union all
    select 'A' || tarjeta_am, cast(null as bigint),
           tarjeta_am, 'AEROMETRO', fecha_hora, monto_gtq, zona_canonica
    from main_silver.silver_am_boardings
"""


def conectar(read_only=True):
    return duckdb.connect(DB_PATH, read_only=read_only)


def preparar_vistas(con, datos_hasta=None):
    """Crea las vistas temporales de eventos y CDC, recortadas si se pide."""
    filtro_ev = ""
    filtro_cdc = ""
    if datos_hasta is not None:
        hasta = pd.Timestamp(datos_hasta).strftime("%Y-%m-%d %H:%M:%S")
        filtro_ev = f"where fecha_hora < timestamp '{hasta}'"
        filtro_cdc = f"where commit_ts < timestamp '{hasta}'"
    con.execute(f"create or replace temp view ev as select * from ({_EVENTOS_SQL}) {filtro_ev}")
    con.execute(f"create or replace temp view cdc as select * from main_silver.silver_cdc_padron {filtro_cdc}")


def construir(con, corte: date, con_etiqueta: bool = True) -> pd.DataFrame:
    """Una fila por unidad de la poblacion del corte, con features y etiqueta."""
    t = datetime.combine(corte, datetime.min.time())
    ini = t - timedelta(days=VENTANA_DIAS)
    fin_etiqueta = t + timedelta(days=HORIZONTE_DIAS)

    if con_etiqueta:
        max_dato = con.execute("select max(fecha_hora) from ev").fetchone()[0]
        if max_dato is None or max_dato < fin_etiqueta - timedelta(days=1):
            raise ValueError(f"No hay datos suficientes para la etiqueta del corte {corte}")

    p = {"t": t, "ini": ini, "fin": fin_etiqueta}
    sql = f"""
    with ventana as (
        select * from ev where fecha_hora >= $ini and fecha_hora < $t
    ),
    dias as (
        select unidad_id, cast(fecha_hora as date) as dia from ventana group by 1, 2
    ),
    huecos as (
        select unidad_id,
               max(date_diff('day', dia_prev, dia) - 1) as max_hueco
        from (select unidad_id, dia, lag(dia) over (partition by unidad_id order by dia) as dia_prev from dias)
        group by 1
    ),
    agg as (
        select
            unidad_id,
            any_value(numero) as numero,
            count(*) as viajes_28d,
            count(*) filter (where fecha_hora >= $t - interval 7 day) as viajes_7d,
            count(*) filter (where fecha_hora >= $t - interval 14 day) as viajes_14d,
            count(*) filter (where fecha_hora < $t - interval 14 day) as viajes_prev_14d,
            count(distinct cast(fecha_hora as date)) as dias_activos_28d,
            date_diff('second', max(fecha_hora), $t) / 86400.0 as dias_desde_ultimo_viaje,
            count(distinct operador) as n_operadores,
            count(distinct tarjeta) as n_tarjetas,
            count(distinct zona) as n_zonas,
            avg(case when operador = 'TRANSMETRO' then 1.0 else 0.0 end) as prop_transmetro,
            avg(case when operador = 'TRANSURBANO' then 1.0 else 0.0 end) as prop_transurbano,
            avg(case when operador = 'METRORIEL' then 1.0 else 0.0 end) as prop_metroriel,
            avg(case when operador = 'AEROMETRO' then 1.0 else 0.0 end) as prop_aerometro,
            avg(case when extract(hour from fecha_hora) in (5, 6, 7, 8, 16, 17, 18, 19) then 1.0 else 0.0 end) as prop_hora_pico,
            avg(case when dayofweek(fecha_hora) in (0, 6) then 1.0 else 0.0 end) as prop_fin_de_semana,
            sum(monto_gtq) as gasto_28d,
            avg(monto_gtq) as tarifa_promedio
        from ventana
        group by 1
    ),
    cdc_ultimo as (
        select numero, op, perfil,
               row_number() over (partition by numero order by seq desc) as rn
        from cdc where numero is not null and commit_ts < $t
    ),
    perfil_vigente as (
        select numero, perfil,
               row_number() over (partition by numero order by seq desc) as rn
        from cdc where numero is not null and commit_ts < $t and op in ('INSERT', 'UPDATE')
    ),
    futuro as (
        select distinct unidad_id from ev where fecha_hora >= $t and fecha_hora < $fin
    ),
    tarjetas_previas as (
        select unidad_id, string_agg(distinct tarjeta, ';' order by tarjeta) as tarjetas
        from ev where fecha_hora < $t group by 1
    )
    select
        a.unidad_id,
        cast($t as date) as fecha_corte,
        tp.tarjetas,
        a.viajes_28d, a.viajes_7d, a.viajes_14d,
        (a.viajes_14d + 1.0) / (a.viajes_prev_14d + 1.0) as tendencia_14d,
        a.dias_activos_28d, a.dias_desde_ultimo_viaje,
        coalesce(h.max_hueco, 0) as max_dias_sin_viajar,
        a.viajes_28d * 1.0 / a.dias_activos_28d as viajes_por_dia_activo,
        a.n_operadores, a.n_tarjetas, a.n_zonas,
        a.prop_transmetro, a.prop_transurbano, a.prop_metroriel, a.prop_aerometro,
        a.prop_hora_pico, a.prop_fin_de_semana, a.gasto_28d, a.tarifa_promedio,
        coalesce(pv.perfil, 'sin_padron') as perfil,
        {"case when f.unidad_id is null then 1 else 0 end" if con_etiqueta else "cast(null as integer)"} as etiqueta
    from agg a
    left join huecos h on h.unidad_id = a.unidad_id
    left join cdc_ultimo cu on cu.numero = a.numero and cu.rn = 1
    left join perfil_vigente pv on pv.numero = a.numero and pv.rn = 1
    left join futuro f on f.unidad_id = a.unidad_id
    left join tarjetas_previas tp on tp.unidad_id = a.unidad_id
    where a.viajes_28d >= {MIN_VIAJES_POBLACION}
      and coalesce(cu.op, '') != 'DELETE'
    order by a.unidad_id
    """
    df = con.execute(sql, p).df()
    df["fecha_corte"] = pd.to_datetime(df["fecha_corte"]).dt.date
    return df


def tabla_cortes(cortes: dict, datos_hasta=None) -> pd.DataFrame:
    """Calcula varios cortes con el mismo codigo y los apila en una tabla."""
    con = conectar()
    try:
        preparar_vistas(con, datos_hasta)
        partes = []
        max_dato = con.execute("select max(fecha_hora) from ev").fetchone()[0]
        for nombre, corte in cortes.items():
            fin = datetime.combine(corte, datetime.min.time()) + timedelta(days=HORIZONTE_DIAS)
            con_etiqueta = max_dato is not None and max_dato >= fin - timedelta(days=1)
            df = construir(con, corte, con_etiqueta=con_etiqueta)
            df.insert(1, "corte", nombre)
            partes.append(df)
        return pd.concat(partes, ignore_index=True)
    finally:
        con.close()
