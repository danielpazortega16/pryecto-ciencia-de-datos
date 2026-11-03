"""Convierte un informe Markdown de docs/proyecto2 a PDF (Chrome sin ventana).

La primera linea del Markdown (# Titulo) se usa como titulo de la portada.
Con --compacto no hay portada, solo un encabezado arriba, para que la ficha
quepa en una pagina.

Uso:
    python -m ml.informe_pdf docs/proyecto2/informe_fase1.md
    python -m ml.informe_pdf docs/proyecto2/ficha_modelo.md --compacto
"""
import os
import subprocess
import sys
from datetime import date

import markdown

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
CATEDRATICO = "Ing. Max Cerna"
CURSO = "Ciencia de Datos"
SEMESTRE = "Segundo semestre 2026"
PROYECTO = "¿Quién deja de usar la red?"
INTEGRANTES = [("José Daniel Paz Ortega", "1200022"), ("Jonathan García", "1045222")]

ESTILO = """
@page { size: Letter; margin: 2.5cm 2.5cm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; line-height: 1.5; color: #000; }
h2 { font-size: 14pt; font-weight: bold; margin: 22px 0 6px 0; }
h3 { font-size: 12pt; font-weight: bold; margin: 16px 0 4px 0; }
p { margin: 6px 0 8px 0; text-align: justify; }
table { border-collapse: collapse; margin: 8px 0 12px 0; font-size: 9.5pt; line-height: 1.3; }
th, td { border: 1px solid #777; padding: 3px 7px; vertical-align: top; }
th { font-weight: bold; }
pre { font-family: Consolas, monospace; font-size: 10pt; margin: 6px 0 10px 1.5em; white-space: pre-wrap; }
code { font-family: inherit; }
pre code { font-family: Consolas, monospace; }
img { display: block; max-width: 85%; margin: 8px auto 12px auto; }
.portada { height: 22cm; position: relative; page-break-after: always; }
.portada .datos { position: absolute; top: 0; left: 0; line-height: 1.6; }
.portada .logo { position: absolute; top: 0; right: 0; width: 5.6cm; margin: 0; }
.portada .titulo { position: absolute; top: 8.5cm; width: 100%; text-align: center; font-size: 24pt; }
.portada .subtitulo { position: absolute; top: 10.2cm; width: 100%; text-align: center; font-size: 14pt; }
.portada .nombres { position: absolute; top: 14.5cm; right: 0; text-align: right; line-height: 1.6; }
.portada .fecha { position: absolute; top: 20cm; width: 100%; text-align: center; }
.encabezado { line-height: 1.45; margin-bottom: 10px; }
"""

COMPACTO = """
@page { size: Letter; margin: 1.4cm 1.8cm; }
body { font-size: 9pt; line-height: 1.3; }
h3 { font-size: 9.8pt; margin: 7px 0 1px 0; }
p, ul { margin: 2px 0 3px 0; }
ul { padding-left: 1.4em; }
table { font-size: 8.5pt; margin: 3px 0 4px 0; }
pre { font-size: 9pt; margin: 2px 0 4px 1.5em; }
"""


def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def portada(titulo, fecha):
    datos = "<br>".join([CATEDRATICO, CURSO, SEMESTRE])
    nombres = "<br>".join(f"{n}<br>carné: {c}" for n, c in INTEGRANTES)
    return (f"<div class='portada'><div class='datos'>{datos}</div>"
            f"<img class='logo' src='logo_url.png' alt=''>"
            f"<div class='titulo'>{titulo}</div><div class='subtitulo'>{PROYECTO}</div>"
            f"<div class='nombres'>{nombres}</div><div class='fecha'>{fecha}</div></div>")


def encabezado(titulo, fecha):
    nombres = " y ".join(f"{n} - {c}" for n, c in INTEGRANTES)
    return (f"<div class='encabezado'>{nombres}<br>{CURSO}<br>Ingeniero: {CATEDRATICO[5:]}<br>"
            f"<b>{titulo}</b> {fecha}</div>")


def main(ruta_md, compacto=False):
    ruta_md = os.path.abspath(ruta_md)
    with open(ruta_md, encoding="utf-8") as f:
        lineas = f.read().split("\n")
    titulo = lineas[0].lstrip("# ").strip()
    cuerpo = markdown.markdown("\n".join(lineas[1:]), extensions=["tables", "fenced_code"])
    fecha = fecha_larga(date.today())
    inicio = encabezado(titulo, fecha) if compacto else portada(titulo, fecha)
    ruta_html = ruta_md[:-3] + ".html"
    ruta_pdf = ruta_md[:-3] + ".pdf"
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
                f"<style>{ESTILO}{COMPACTO if compacto else ''}</style></head>"
                f"<body>{inicio}{cuerpo}</body></html>")
    perfil = os.path.join(os.environ.get("TEMP", "."), "chrome_pdf_informes")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}",
                    "--no-pdf-header-footer", f"--print-to-pdf={ruta_pdf}", "file:///" + ruta_html.replace("\\", "/")],
                   check=True, capture_output=True)
    os.remove(ruta_html)
    print(ruta_pdf)


if __name__ == "__main__":
    main(sys.argv[1], compacto="--compacto" in sys.argv)
