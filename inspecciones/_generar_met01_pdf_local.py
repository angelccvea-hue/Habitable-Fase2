"""
Genera PDF MET-01 (estandarización de partidas/metrados) con el mismo arte que PLN-01.
Microsoft Edge headless --print-to-pdf.
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

from inspecciones.ficha_metrados_estandarizacion import ficha_met01  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")


def _edge() -> Path:
    for p in (EDGE, EDGE_ALT):
        if p.is_file():
            return p
    raise FileNotFoundError("Microsoft Edge no encontrado para imprimir PDF")


def main() -> None:
    ficha = ficha_met01()
    html = render_to_string(
        "inspecciones/ficha_metrados_estandarizacion_pdf.html",
        {
            "ficha": ficha,
            "generado": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
        },
    )
    html_path = DOWNLOADS / "MET-01-estandarizacion-partidas-metrados.html"
    pdf_path = DOWNLOADS / "MET-01-estandarizacion-partidas-metrados.pdf"
    html_path.write_text(html, encoding="utf-8")

    edge = _edge()
    cmd = [
        str(edge),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not pdf_path.is_file():
        print("stderr:", r.stderr)
        print("stdout:", r.stdout)
        raise SystemExit(f"Edge falló (code={r.returncode})")

    print("HTML", html_path)
    print("PDF ", pdf_path, f"({pdf_path.stat().st_size} bytes)")
    print("partidas", len(ficha.get("filas_catalogo") or []))


if __name__ == "__main__":
    main()
