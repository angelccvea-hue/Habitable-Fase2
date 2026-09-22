"""
Genera PDF único PLN-01 con diagramas SVG estilo Carimar (sin WeasyPrint).
Usa plantilla Django + Microsoft Edge headless --print-to-pdf.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.template.loader import render_to_string  # noqa: E402
from django.utils import timezone  # noqa: E402

from inspecciones.fichas_procedimientos import REFERENCIAS_COMUNES, ficha_para  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")


def _edge() -> Path:
    for p in (EDGE, EDGE_ALT):
        if p.is_file():
            return p
    raise FileNotFoundError("Microsoft Edge no encontrado para imprimir PDF")


def main() -> None:
    ficha = ficha_para("PLN-01")
    if not ficha:
        raise SystemExit("Ficha PLN-01 no encontrada")

    # Verificar que los diagramas van como SVG Carimar, no matriz
    ej0 = (ficha.get("ejemplos_irregulares") or [{}])[0]
    if not ej0.get("svg_html"):
        raise SystemExit("Falta svg_html en ejemplos — abortando")
    me = (ficha.get("mapa_estilo") or {}).get("mini_ejemplo") or {}
    if not me.get("svg_html"):
        raise SystemExit("Falta svg_html en mini_ejemplo — abortando")

    html = render_to_string(
        "inspecciones/ficha_procedimiento_pdf.html",
        {
            "ficha": ficha,
            "referencias": REFERENCIAS_COMUNES,
            "generado": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
            "grid_nums": ["7", "6", "5", "4", "3", "2", "1"],
        },
    )
    # Base URL local para recursos; SVG es inline
    html_path = DOWNLOADS / "PLN-01-plano-inspeccion-ejes.html"
    pdf_path = DOWNLOADS / "PLN-01-plano-inspeccion-ejes.pdf"
    html_path.write_text(html, encoding="utf-8")

    edge = _edge()
    # file:/// URL
    url = html_path.resolve().as_uri()
    cmd = [
        str(edge),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not pdf_path.is_file():
        print("stderr:", r.stderr)
        print("stdout:", r.stdout)
        raise SystemExit(f"Edge falló (code={r.returncode})")

    print("HTML", html_path)
    print("PDF ", pdf_path, f"({pdf_path.stat().st_size} bytes)")
    # Confirmación rápida: el HTML fuente no debe tener celdas tipo grid-demo con B/C
    if 'class="grid-demo"' in html:
        print("AVISO: aún hay grid-demo en plantilla")
    if "plano-svg" in html and "<svg" in html:
        print("OK diagramas SVG embebidos en el documento")


if __name__ == "__main__":
    main()
