"""Genera vista previa HTML + regenera DXF PLN-01 en Descargas."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inspecciones.fichas_procedimientos import ficha_para  # noqa: E402
from inspecciones.plantilla_pln01_dxf import generar  # noqa: E402

DOWNLOADS = Path.home() / "Downloads"


def main() -> None:
    f = ficha_para("PLN-01")
    assert f and f["ejemplos_irregulares"][0].get("svg_html")

    parts = [
        "<!DOCTYPE html><html><head><meta charset=utf-8>",
        "<title>PLN-01 diagramas estilo Carimar</title>",
        "<style>body{font-family:Arial;margin:24px;color:#1a2332}",
        "h1,h2{color:#00247d}.box{margin:20px 0;border:1px solid #cbd5e1;",
        "padding:12px;border-radius:6px}</style></head><body>",
        "<h1>PLN-01 — diagramas (estilo Carimar)</h1>",
        "<p>Misma simbología que el plano de campo: cuadrado azul, "
        "círculos A/B-C, tramos, flecha, orientación.</p>",
    ]
    me = f["mapa_estilo"]["mini_ejemplo"]
    parts.append(
        "<div class=box><h2>Mini-ejemplo mapa de estilo</h2>"
        f"{me['svg_html']}<p>{me.get('nota_pie','')}</p></div>"
    )
    for ej in f["ejemplos_irregulares"]:
        parts.append(
            f"<div class=box><h2>{ej['nombre']}</h2>"
            f"{ej['svg_html']}<p>{ej.get('nota_pie','')}</p></div>"
        )
    parts.append("</body></html>")

    html_out = DOWNLOADS / "PLN-01-diagramas-estilo-carimar.html"
    html_out.write_text("".join(parts), encoding="utf-8")
    print("HTML", html_out)

    dxf = generar()
    shutil.copy(dxf, DOWNLOADS / dxf.name)
    print("DXF", DOWNLOADS / dxf.name)


if __name__ == "__main__":
    main()
