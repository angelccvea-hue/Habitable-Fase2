"""
Plantilla CAD (DXF) para PLN-01 — estilo Carimar / mapa de estilo.

Formato: DXF R2010. Capas PLN-01 + simbología de campo:
  cuadrado azul = columna, círculo amarillo/rojo = severidad,
  rectángulo = tramo, magenta = flecha, orientación N/S/E/O.
"""
from __future__ import annotations

from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

LAYERS = {
    "EJES": {"color": colors.MAGENTA, "linetype": "DASHED"},
    "COLUMNAS": {"color": colors.BLUE, "linetype": "CONTINUOUS"},
    "VIGAS": {"color": colors.CYAN, "linetype": "CONTINUOUS"},
    "MUROS": {"color": 8, "linetype": "CONTINUOUS"},
    "DANOS": {"color": colors.RED, "linetype": "CONTINUOUS"},
    "NORTE": {"color": colors.RED, "linetype": "CONTINUOUS"},
    "ROTULO": {"color": colors.BLUE, "linetype": "CONTINUOUS"},
    "LEYENDA": {"color": 7, "linetype": "CONTINUOUS"},
    "COTAS": {"color": 8, "linetype": "CONTINUOUS"},
    "TEXTO": {"color": 7, "linetype": "CONTINUOUS"},
}

# Retícula A–C × 1–7 (mismo ejemplo Carimar de la ficha)
COLS = [("A", 0.0), ("B", 5.0), ("C", 10.0)]
ROWS = [
    ("1", 0.0),
    ("2", 4.5),
    ("3", 9.0),
    ("4", 13.5),
    ("5", 18.0),
    ("6", 22.5),
    ("7", 27.0),
]

# Severidad por nudo (como Carimar: rojo en 6/7 bordes; resto amarillo)
NODOS_NIVEL = {
    ("A", "7"): "bc",
    ("B", "7"): "a",
    ("C", "7"): "bc",
    ("A", "6"): "bc",
    ("B", "6"): "a",
    ("C", "6"): "bc",
}
# Resto → "a" (amarillo) por defecto al dibujar

TRAMOS = [
    # fila, de, a, nivel
    ("7", "A", "B", "bc"),
    ("7", "B", "C", "bc"),
    ("6", "A", "B", "bc"),
    ("6", "B", "C", "bc"),
    ("2", "A", "B", "a"),
    ("1", "A", "B", "bc"),
    ("1", "B", "C", "bc"),
]

FLECHAS = [
    ("B", "6", "7"),
    ("B", "2", "3"),
]

OUT_NAME = "PLN-01-plano-inspeccion-ejes.dxf"


def _plantillas_dir() -> Path:
    return Path(__file__).resolve().parent / "static" / "plantillas"


def _ensure_linetypes(doc) -> None:
    if "DASHED" not in doc.linetypes:
        doc.linetypes.add(
            "DASHED",
            pattern=[0.5, 0.25, -0.25],
            description="Dashed __ __ __",
        )


def _add_layers(doc) -> None:
    for name, cfg in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=cfg["color"], linetype=cfg["linetype"])


def _bubble(msp, x: float, y: float, label: str, *, r: float = 0.45) -> None:
    msp.add_circle((x, y), r, dxfattribs={"layer": "EJES", "color": colors.MAGENTA})
    msp.add_text(
        label,
        height=0.35,
        dxfattribs={"layer": "EJES", "color": colors.MAGENTA},
    ).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


def _columna(msp, x: float, y: float, *, side: float = 0.5) -> None:
    h = side / 2
    msp.add_lwpolyline(
        [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h), (x - h, y - h)],
        close=True,
        dxfattribs={"layer": "COLUMNAS", "color": colors.BLUE},
    )


def _anillo_severidad(msp, x: float, y: float, nivel: str) -> None:
    col = colors.YELLOW if nivel == "a" else colors.RED
    msp.add_circle((x, y), 0.95, dxfattribs={"layer": "DANOS", "color": col})


def _tramo(msp, x0: float, y: float, x1: float, nivel: str) -> None:
    col = colors.YELLOW if nivel == "a" else colors.RED
    if x1 < x0:
        x0, x1 = x1, x0
    msp.add_lwpolyline(
        [
            (x0 + 0.7, y - 0.28),
            (x1 - 0.7, y - 0.28),
            (x1 - 0.7, y + 0.28),
            (x0 + 0.7, y + 0.28),
        ],
        close=True,
        dxfattribs={"layer": "DANOS", "color": col},
    )


def _flecha(msp, x: float, y: float) -> None:
    msp.add_lwpolyline(
        [(x - 1.0, y - 0.4), (x + 1.0, y - 0.4), (x + 1.0, y + 0.4), (x - 1.0, y + 0.4)],
        close=True,
        dxfattribs={"layer": "DANOS", "color": colors.MAGENTA},
    )
    msp.add_text(
        "Flecha",
        height=0.32,
        dxfattribs={"layer": "DANOS", "color": colors.MAGENTA},
    ).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


def _orientacion(msp, x_min, x_max, y_min, y_max) -> None:
    # Como Carimar: OESTE arriba, ESTE abajo, SUR izq, NORTE der
    mid_x = (x_min + x_max) / 2
    mid_y = (y_min + y_max) / 2
    attrs = {"layer": "NORTE", "color": colors.RED}
    msp.add_text("OESTE", height=0.45, dxfattribs=attrs).set_placement(
        (mid_x, y_max + 3.2), align=TextEntityAlignment.BOTTOM_CENTER
    )
    msp.add_text("ESTE", height=0.45, dxfattribs=attrs).set_placement(
        (mid_x, y_min - 3.2), align=TextEntityAlignment.TOP_CENTER
    )
    msp.add_text("SUR", height=0.45, dxfattribs=attrs).set_placement(
        (x_min - 3.6, mid_y), align=TextEntityAlignment.MIDDLE_CENTER
    )
    msp.add_text("NORTE", height=0.45, dxfattribs=attrs).set_placement(
        (x_max + 3.6, mid_y), align=TextEntityAlignment.MIDDLE_CENTER
    )


def _cajetin(msp, x0: float, y0: float, w: float = 14.0, h: float = 5.5) -> None:
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True,
        dxfattribs={"layer": "ROTULO", "color": colors.BLUE},
    )
    for dy in (1.1, 2.2, 3.3, 4.4):
        msp.add_line(
            (x0, y0 + dy),
            (x0 + w, y0 + dy),
            dxfattribs={"layer": "ROTULO", "color": colors.BLUE},
        )
    msp.add_line(
        (x0 + w * 0.55, y0),
        (x0 + w * 0.55, y0 + h),
        dxfattribs={"layer": "ROTULO", "color": colors.BLUE},
    )

    def cell(tx, ty, text, height=0.28):
        msp.add_text(
            text, height=height, dxfattribs={"layer": "ROTULO", "color": colors.BLUE}
        ).set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_LEFT)

    cell(x0 + 0.25, y0 + h - 0.55, "CPEH — Fase II ROJO · PLN-01", 0.32)
    cell(x0 + w * 0.55 + 0.2, y0 + h - 0.55, "Rev. borrador", 0.28)
    cell(x0 + 0.25, y0 + 3.85, "Edificio: ______________________________")
    cell(x0 + w * 0.55 + 0.2, y0 + 3.85, "ID Habitable: __________")
    cell(x0 + 0.25, y0 + 2.75, "Plano: inspección estructural — planta ______")
    cell(x0 + w * 0.55 + 0.2, y0 + 2.75, "Piso: PB / P__")
    cell(x0 + 0.25, y0 + 1.65, "Estilo: Carimar / mapa PLN-01")
    cell(x0 + w * 0.55 + 0.2, y0 + 1.65, "Fecha: ____/____/______")
    cell(x0 + 0.25, y0 + 0.55, "Elaboró: ____________________")
    cell(x0 + w * 0.55 + 0.2, y0 + 0.55, "Revisó: ____________________")


def _leyenda(msp, x0: float, y0: float) -> None:
    msp.add_text(
        "LEYENDA (mapa de estilo PLN-01)",
        height=0.35,
        dxfattribs={"layer": "LEYENDA"},
    ).set_placement((x0, y0 + 8.5), align=TextEntityAlignment.BOTTOM_LEFT)
    items = [
        (colors.BLUE, "box", "Columna / nudo (cuadrado azul)"),
        (colors.YELLOW, "circ", "Daño leve A (círculo amarillo)"),
        (colors.RED, "circ", "Daño B/C (círculo rojo)"),
        (colors.YELLOW, "rect", "Tramo viga/muro leve (A)"),
        (colors.RED, "rect", "Tramo viga/muro B/C"),
        (colors.MAGENTA, "rect", "Flecha / deflexión"),
        (colors.MAGENTA, "circ", "Burbuja de eje"),
    ]
    y = y0 + 7.8
    for col, kind, desc in items:
        if kind == "box":
            msp.add_lwpolyline(
                [(x0, y - 0.2), (x0 + 0.4, y - 0.2), (x0 + 0.4, y + 0.2), (x0, y + 0.2)],
                close=True,
                dxfattribs={"layer": "LEYENDA", "color": col},
            )
        elif kind == "circ":
            msp.add_circle((x0 + 0.2, y), 0.22, dxfattribs={"layer": "LEYENDA", "color": col})
        else:
            msp.add_lwpolyline(
                [(x0, y - 0.15), (x0 + 0.55, y - 0.15), (x0 + 0.55, y + 0.15), (x0, y + 0.15)],
                close=True,
                dxfattribs={"layer": "LEYENDA", "color": col},
            )
        msp.add_text(desc, height=0.22, dxfattribs={"layer": "LEYENDA"}).set_placement(
            (x0 + 0.75, y), align=TextEntityAlignment.MIDDLE_LEFT
        )
        y -= 0.9


def build_doc() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6
    doc.header["$MEASUREMENT"] = 1
    _ensure_linetypes(doc)
    _add_layers(doc)
    msp = doc.modelspace()

    cx = {k: v for k, v in COLS}
    ry = {k: v for k, v in ROWS}
    xs = list(cx.values())
    ys = list(ry.values())
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    margin = 1.8

    msp.add_text(
        "RESIDENCIAS CARIMAR I — PLANTILLA PLN-01 (ejemplo didáctico)",
        height=0.5,
        dxfattribs={"layer": "ROTULO", "color": 5},
    ).set_placement(
        ((x_min + x_max) / 2, y_max + margin + 2.0),
        align=TextEntityAlignment.BOTTOM_CENTER,
    )
    msp.add_text(
        "Sustituir título y retícula por el edificio real · mismos símbolos",
        height=0.28,
        dxfattribs={"layer": "TEXTO"},
    ).set_placement(
        ((x_min + x_max) / 2, y_max + margin + 1.2),
        align=TextEntityAlignment.BOTTOM_CENTER,
    )

    for letter, x in COLS:
        msp.add_line(
            (x, y_min - margin),
            (x, y_max + margin),
            dxfattribs={"layer": "EJES", "color": colors.MAGENTA, "linetype": "DASHED"},
        )
        _bubble(msp, x, y_max + margin + 0.2, letter)
        _bubble(msp, x, y_min - margin - 0.2, letter)

    for num, y in ROWS:
        msp.add_line(
            (x_min - margin, y),
            (x_max + margin, y),
            dxfattribs={"layer": "EJES", "color": colors.MAGENTA, "linetype": "DASHED"},
        )
        _bubble(msp, x_min - margin - 0.2, y, num)
        _bubble(msp, x_max + margin + 0.2, y, num)

    # Tramos primero (debajo visual de nodos)
    for fila, de, a, nivel in TRAMOS:
        _tramo(msp, cx[de], ry[fila], cx[a], nivel)

    for eje, r0, r1 in FLECHAS:
        y = (ry[r0] + ry[r1]) / 2
        _flecha(msp, cx[eje], y)

    # Columnas + anillos
    for letter, x in COLS:
        for num, y in ROWS:
            _columna(msp, x, y)
            nivel = NODOS_NIVEL.get((letter, num), "a")
            _anillo_severidad(msp, x, y, nivel)

    _orientacion(msp, x_min, x_max, y_min, y_max)

    # Entrada cerca de C1
    msp.add_text(
        "Entrada",
        height=0.35,
        dxfattribs={"layer": "TEXTO"},
    ).set_placement(
        (cx["C"] + 1.2, ry["1"] - 0.9), align=TextEntityAlignment.MIDDLE_LEFT
    )

    _leyenda(msp, x_max + 5.5, y_min + 6)
    _cajetin(msp, x_min - 1.0, y_min - 9.5)

    msp.add_text(
        "IDs: PB-B6 · PB-V(A-B)·eje6 · PB-FLECHA·B·entre6-7  |  "
        "Capas: EJES COLUMNAS VIGAS MUROS DANOS NORTE ROTULO",
        height=0.22,
        dxfattribs={"layer": "TEXTO"},
    ).set_placement((x_min - 1.0, y_min - 10.2), align=TextEntityAlignment.TOP_LEFT)

    return doc


def generar(destino: Path | None = None) -> Path:
    out_dir = _plantillas_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(destino) if destino else out_dir / OUT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    build_doc().saveas(path)
    return path


if __name__ == "__main__":
    print(f"OK {generar()}")
