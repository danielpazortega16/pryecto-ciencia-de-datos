"""Convierte un informe Markdown de docs/proyecto2 a PDF (Chrome sin ventana).

Uso:
    python -m ml.informe_pdf docs/proyecto2/informe_fase1.md
"""
import os
import subprocess
import sys

import markdown

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ESTILO = """
@page { size: Letter; margin: 2cm 2.2cm; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt; line-height: 1.4; color: #1a1a1a; }
h1 { font-size: 16pt; font-weight: normal; border-bottom: 1px solid #888; padding-bottom: 4px; }
h2 { font-size: 12.5pt; margin-top: 16px; }
table { border-collapse: collapse; margin: 6px 0 10px 0; font-size: 9.5pt; }
th, td { border: 1px solid #bbb; padding: 3px 6px; vertical-align: top; }
th { background: #f0f0f0; }
code, pre { font-family: Consolas, monospace; font-size: 9pt; background: #f5f5f5; }
pre { padding: 6px; }
img { max-width: 100%; }
"""


def main(ruta_md):
    ruta_md = os.path.abspath(ruta_md)
    with open(ruta_md, encoding="utf-8") as f:
        cuerpo = markdown.markdown(f.read(), extensions=["tables", "fenced_code"])
    ruta_html = ruta_md[:-3] + ".html"
    ruta_pdf = ruta_md[:-3] + ".pdf"
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(f"<!doctype html><html lang='es'><head><meta charset='utf-8'><style>{ESTILO}</style></head><body>{cuerpo}</body></html>")
    perfil = os.path.join(os.environ.get("TEMP", "."), "chrome_pdf_informes")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}",
                    "--no-pdf-header-footer", f"--print-to-pdf={ruta_pdf}", "file:///" + ruta_html.replace("\\", "/")],
                   check=True, capture_output=True)
    os.remove(ruta_html)
    print(ruta_pdf)


if __name__ == "__main__":
    main(sys.argv[1])
