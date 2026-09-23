"""
Generador de datos sinteticos para el proyecto Agencia Metropolitana de Transporte.

No es el script oficial del curso (no fue entregado a tiempo para la Fase 1).
Replica las inconsistencias descritas en el enunciado para que el problema de
integracion sea real: formatos de fecha, moneda, llave de usuario y zona
distintos por operador, mas los defectos de calidad que pide inyectar
(duplicados de torniquete, codigos de parada nulos, fechas futuras, viajes
sin salida).

Uso:
    python generar_red_metropolitana.py [ESCALA]

ESCALA por defecto 0.02 (~unos miles de filas por archivo, corre en segundos).
ESCALA 1.0 se acerca al tamano real descrito en el enunciado (~2.5 GB) y no
es necesario llegar hasta ahi para la Fase 1.
"""
import csv
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

random.seed(42)

ESCALA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_red")
os.makedirs(OUT_DIR, exist_ok=True)

FECHA_INICIO = datetime(2026, 8, 1)
DIAS_HISTORIA = 30

ZONAS_METRORIEL = ["Zona 12", "Zona 8", "Zona 1", "Zona 6", "Zona 17"]
TODAS_ZONAS = [f"Zona {i}" for i in range(1, 22)]

# ---------------------------------------------------------------------------
# Catalogos
# ---------------------------------------------------------------------------

def gen_tm_estaciones():
    path = os.path.join(OUT_DIR, "tm_estaciones.csv")
    lineas = [f"Linea {i}" for i in range(1, 9)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["linea_id", "nombre_linea", "estacion_id", "nombre_estacion", "zona"])
        est_id = 1
        for i, linea in enumerate(lineas, start=1):
            n_estaciones = random.randint(8, 16)
            for _ in range(n_estaciones):
                zona = random.choice(TODAS_ZONAS)
                w.writerow([i, linea, est_id, f"Estacion {est_id}", zona])
                est_id += 1
    return path


def gen_tu_paradas():
    path = os.path.join(OUT_DIR, "tu_paradas.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta_id", "nombre_ruta", "parada_id", "nombre_parada", "zona"])
        parada_id = 1
        for ruta in range(1, 42):
            n_paradas = random.randint(6, 14)
            for _ in range(n_paradas):
                zona_num = random.randint(1, 21)
                zona = f"Z{zona_num}"  # Transurbano: mayusculas abreviadas
                w.writerow([ruta, f"Ruta {ruta}", parada_id, f"Parada {parada_id}", zona])
                parada_id += 1
    return path


def gen_mr_estaciones():
    path = os.path.join(OUT_DIR, "mr_estaciones.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estacion_id", "nombre_estacion", "orden", "zona"])
        for i in range(1, 23):
            zona = ZONAS_METRORIEL[min(i // 5, len(ZONAS_METRORIEL) - 1)]
            w.writerow([i, f"Estacion MetroRiel {i}", i, zona])
    return path


def gen_am_estaciones():
    path = os.path.join(OUT_DIR, "am_estaciones.csv")
    distritos = ["district-10", "district-01"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["eje_id", "nombre_eje", "district"])
        for i, d in enumerate(distritos, start=1):
            w.writerow([i, f"Eje {i}", d])
    return path


# ---------------------------------------------------------------------------
# Usuarios base (para poder simular reuso de tarjeta / transbordo)
# ---------------------------------------------------------------------------

N_USUARIOS = max(200, int(5000 * ESCALA))
usuarios_tm = [f"TC-{str(i).zfill(8)}" for i in range(1, N_USUARIOS + 1)]
usuarios_tu = [str(i).zfill(10) for i in range(1, N_USUARIOS + 1)]
usuarios_mr = [f"MR{str(i).zfill(7)}" for i in range(1, N_USUARIOS + 1)]
usuarios_am = [hashlib.sha256(f"am-user-{i}".encode()).hexdigest()[:12] for i in range(1, N_USUARIOS + 1)]


def random_fecha_hora():
    dia = random.randint(0, DIAS_HISTORIA - 1)
    hora = random.choices(
        range(24),
        weights=[1, 1, 1, 1, 1, 2, 6, 10, 10, 4, 3, 3, 4, 4, 3, 3, 6, 10, 8, 4, 2, 2, 1, 1],
    )[0]
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return FECHA_INICIO + timedelta(days=dia, hours=hora, minutes=minuto, seconds=segundo)


# ---------------------------------------------------------------------------
# Transmetro: validaciones (abordaje). Fecha YYYY-MM-DD HH:MM:SS, quetzales,
# zona "Zona 10". Se inyectan duplicados de torniquete y fechas futuras.
# ---------------------------------------------------------------------------

def gen_transmetro_validaciones():
    path = os.path.join(OUT_DIR, "transmetro_validaciones.csv")
    n = max(2000, int(80000 * ESCALA))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["validacion_id", "tarjeta_id", "fecha_hora", "estacion_id", "zona", "monto"])
        vid = 1
        rows = []
        for _ in range(n):
            fh = random_fecha_hora()
            row = [
                vid,
                random.choice(usuarios_tm),
                fh.strftime("%Y-%m-%d %H:%M:%S"),
                random.randint(1, 100),
                "Zona 10",
                2.50,
            ]
            rows.append(row)
            vid += 1
        # Duplicados de torniquete: misma tarjeta y estacion, milisegundos despues
        for _ in range(max(5, int(n * 0.01))):
            base = random.choice(rows)
            dup = base.copy()
            dup[0] = vid
            rows.append(dup)
            vid += 1
        # Fechas del futuro (reloj de torniquete desconfigurado)
        for _ in range(max(3, int(n * 0.002))):
            base = random.choice(rows)
            futura = base.copy()
            futura[0] = vid
            futura[2] = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S")
            rows.append(futura)
            vid += 1
        random.shuffle(rows)
        w.writerows(rows)
    return path, len(rows)


# ---------------------------------------------------------------------------
# Transurbano: transacciones. Fecha y hora en columnas separadas, centavos,
# zona "Z10" mayusculas, llave numerica sin prefijo. Se inyectan codigos de
# parada nulos.
# ---------------------------------------------------------------------------

def gen_transurbano_transacciones():
    path = os.path.join(OUT_DIR, "transurbano_transacciones.csv")
    n = max(2000, int(270000 * ESCALA))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["transaccion_id", "tarjeta_id", "fecha", "hora", "parada_id", "zona", "monto_centavos"])
        for i in range(1, n + 1):
            fh = random_fecha_hora()
            parada = random.randint(1, 400)
            if random.random() < 0.01:
                parada = ""  # codigo de parada nulo
            zona_num = random.randint(1, 21)
            w.writerow([
                str(i).zfill(10),
                random.choice(usuarios_tu),
                fh.strftime("%Y-%m-%d"),
                fh.strftime("%H:%M:%S"),
                parada,
                f"Z{zona_num}",
                150,
            ])
    return path, n


# ---------------------------------------------------------------------------
# MetroRiel: viajes completos (JSON Lines). ISO 8601, quetzales, zona
# "Zona 10". Se inyectan viajes sin estacion de salida (viaje sin cerrar).
# ---------------------------------------------------------------------------

def gen_metroriel_viajes():
    path = os.path.join(OUT_DIR, "metroriel_viajes.jsonl")
    n = max(1000, int(20000 * ESCALA))
    with open(path, "w", encoding="utf-8") as f:
        for i in range(1, n + 1):
            fh = random_fecha_hora()
            duracion_min = 41
            estacion_entrada = random.randint(1, 22)
            estacion_salida = random.randint(1, 22)
            sin_salida = random.random() < 0.008
            zona_entrada = ZONAS_METRORIEL[min(estacion_entrada // 5, len(ZONAS_METRORIEL) - 1)]
            registro = {
                "viaje_id": f"MRV{str(i).zfill(8)}",
                "tarjeta_id": random.choice(usuarios_mr),
                "inicio": fh.isoformat(),
                "fin": None if sin_salida else (fh + timedelta(minutes=duracion_min)).isoformat(),
                "estacion_entrada": estacion_entrada,
                "estacion_salida": None if sin_salida else estacion_salida,
                "zona": zona_entrada,
                "monto": 3.00,
            }
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return path, n


# ---------------------------------------------------------------------------
# Aerometro: boardings. ISO en UTC (no hora local), quetzales, zona
# "district" en ingles, llave = hash de 12 caracteres.
# ---------------------------------------------------------------------------

def gen_aerometro_boardings():
    path = os.path.join(OUT_DIR, "aerometro_boardings.csv")
    n = max(1000, int(15000 * ESCALA))
    districts = ["district-10", "district-01"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["boarding_id", "user_hash", "timestamp_utc", "eje_id", "district", "amount"])
        for i in range(1, n + 1):
            fh_local = random_fecha_hora()
            fh_utc = (fh_local + timedelta(hours=6)).replace(tzinfo=timezone.utc)  # Guatemala = UTC-6
            district = random.choice(districts)
            w.writerow([
                f"AM{str(i).zfill(8)}",
                random.choice(usuarios_am),
                fh_utc.isoformat().replace("+00:00", "Z"),
                districts.index(district) + 1,
                district,
                4.00,
            ])
    return path, n


# ---------------------------------------------------------------------------
# CDC del padron de usuarios de Transmetro: INSERT, UPDATE, DELETE en orden.
# Los DELETE llegan con la llave y sin cuerpo.
# ---------------------------------------------------------------------------

def gen_cdc_padron():
    path = os.path.join(OUT_DIR, "cdc_padron_usuarios.csv")
    eventos = []
    seq = 1
    ts = FECHA_INICIO
    activos = set()
    for tarjeta in usuarios_tm:
        ts += timedelta(seconds=random.randint(1, 120))
        nombre = f"Usuario {tarjeta[-4:]}"
        eventos.append([seq, "INSERT", ts.isoformat(), tarjeta, nombre, "activo"])
        activos.add(tarjeta)
        seq += 1

    # Updates: cambio de nombre o de estado, sobre tarjetas ya existentes
    n_updates = max(20, int(len(usuarios_tm) * 0.15))
    for _ in range(n_updates):
        tarjeta = random.choice(usuarios_tm)
        ts += timedelta(seconds=random.randint(1, 120))
        nombre = f"Usuario {tarjeta[-4:]} (act)"
        eventos.append([seq, "UPDATE", ts.isoformat(), tarjeta, nombre, "activo"])
        seq += 1

    # Deletes: llegan con la llave y sin cuerpo (nombre/estado vacios)
    n_deletes = max(10, int(len(usuarios_tm) * 0.08))
    tarjetas_a_borrar = random.sample(usuarios_tm, n_deletes)
    for tarjeta in tarjetas_a_borrar:
        ts += timedelta(seconds=random.randint(1, 120))
        eventos.append([seq, "DELETE", ts.isoformat(), tarjeta, "", ""])
        seq += 1

    eventos.sort(key=lambda r: r[2])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seq", "operacion", "ts", "tarjeta_id", "nombre", "estado"])
        w.writerows(eventos)
    return path, len(eventos)


def main():
    print(f"Generando datos con ESCALA={ESCALA} en {OUT_DIR}")
    resultados = {}
    resultados["tm_estaciones.csv"] = gen_tm_estaciones()
    resultados["tu_paradas.csv"] = gen_tu_paradas()
    resultados["mr_estaciones.csv"] = gen_mr_estaciones()
    resultados["am_estaciones.csv"] = gen_am_estaciones()
    p, n = gen_transmetro_validaciones()
    resultados["transmetro_validaciones.csv"] = f"{p} ({n} filas)"
    p, n = gen_transurbano_transacciones()
    resultados["transurbano_transacciones.csv"] = f"{p} ({n} filas)"
    p, n = gen_metroriel_viajes()
    resultados["metroriel_viajes.jsonl"] = f"{p} ({n} filas)"
    p, n = gen_aerometro_boardings()
    resultados["aerometro_boardings.csv"] = f"{p} ({n} filas)"
    p, n = gen_cdc_padron()
    resultados["cdc_padron_usuarios.csv"] = f"{p} ({n} filas)"

    for archivo, info in resultados.items():
        print(f"  - {archivo}: {info}")

    total_bytes = sum(
        os.path.getsize(os.path.join(OUT_DIR, f)) for f in os.listdir(OUT_DIR)
    )
    print(f"Tamano total: {total_bytes / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
