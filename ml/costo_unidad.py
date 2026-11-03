"""Costo de la unidad elegida (1.2).

La unidad es la persona. Para medir lo que eso cuesta y lo que evita:

1. Contrafactual con la tarjeta como unidad: se arma la misma poblacion y
   etiqueta pero por tarjeta, y se cuenta cuantos de esos positivos son de
   personas que siguieron viajando con otra tarjeta (mismo numero en otro
   operador). Ese es el error que la persona evita.
2. Aerometro: su llave es un hash que no se puede enlazar, asi que cada
   tarjeta de Aerometro es una persona aparte. Se cuenta cuantas unidades y
   positivos son solo de Aerometro: si alguna de esas personas siguio
   viajando con una tarjeta de otro operador, ahi hay un falso abandono que
   no se puede medir.

Uso:
    python -m ml.costo_unidad
"""
import json
import os
from datetime import datetime, timedelta

from ml.config import CORTES, DOCS_P2, HORIZONTE_DIAS, MIN_VIAJES_POBLACION, VENTANA_DIAS
from ml.features import conectar, construir, preparar_vistas


def contrafactual_tarjeta(con, corte):
    t = datetime.combine(corte, datetime.min.time())
    p = {"t": t, "ini": t - timedelta(days=VENTANA_DIAS), "fin": t + timedelta(days=HORIZONTE_DIAS)}
    sql = f"""
    with pob as (
        select tarjeta, operador, any_value(numero) as numero, any_value(unidad_id) as unidad_id
        from ev where fecha_hora >= $ini and fecha_hora < $t
        group by 1, 2 having count(*) >= {MIN_VIAJES_POBLACION}
    ),
    cdc_ult as (
        select tarjeta, op, row_number() over (partition by tarjeta order by seq desc) rn
        from cdc where commit_ts < $t
    ),
    pob_ok as (
        select p.* from pob p left join cdc_ult c on c.tarjeta = p.tarjeta and c.rn = 1
        where coalesce(c.op, '') != 'DELETE'
    ),
    fut_tarjeta as (select distinct tarjeta from ev where fecha_hora >= $t and fecha_hora < $fin),
    fut_unidad as (select distinct unidad_id from ev where fecha_hora >= $t and fecha_hora < $fin),
    etiquetada as (
        select p.*, (ft.tarjeta is null) as positivo_tarjeta, (fu.unidad_id is not null) as persona_siguio
        from pob_ok p
        left join fut_tarjeta ft on ft.tarjeta = p.tarjeta
        left join fut_unidad fu on fu.unidad_id = p.unidad_id
    )
    select count(*) as poblacion,
           count(*) filter (where positivo_tarjeta) as positivos,
           count(*) filter (where positivo_tarjeta and persona_siguio) as positivos_falsos
    from etiquetada
    """
    pob, pos, falsos = con.execute(sql, p).fetchone()
    return {"poblacion_tarjetas": pob, "positivos_tarjeta": pos, "positivos_de_personas_que_siguieron": falsos,
            "proporcion": round(falsos / pos, 4) if pos else None}


def aerometro(df):
    am = df[df["unidad_id"].str.startswith("A")]
    return {"unidades_solo_aerometro": len(am), "de_la_poblacion": len(df),
            "positivos_solo_aerometro": int(am["etiqueta"].sum()), "positivos_totales": int(df["etiqueta"].sum())}


def main():
    con = conectar()
    preparar_vistas(con)
    resultado = {}
    for nombre in ("A", "B"):
        corte = CORTES[nombre]
        df = construir(con, corte, con_etiqueta=True)
        resultado[nombre] = {"tarjeta_como_unidad": contrafactual_tarjeta(con, corte), "aerometro": aerometro(df)}
    con.close()
    with open(os.path.join(DOCS_P2, "costo_unidad.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
