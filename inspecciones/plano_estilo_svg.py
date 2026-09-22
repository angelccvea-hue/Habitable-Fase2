"""
Diagramas SVG estilo Carimar / mapa PLN-01 (nodos, tramos, flechas, orientación).

Sustituye la antigua matriz de celdas etiquetadas (7A, 7B…) por un plano esquemático
alineado a los ejemplos de campo y a la plantilla DXF.
"""
from __future__ import annotations

from html import escape
from typing import Any


def _nivel_stroke(nivel: str) -> tuple[str, str]:
    n = (nivel or "bc").lower()
    if n in ("a", "leve"):
        return "#ca8a04", "#fef08a"
    return "#dc2626", "#fecaca"


def plano_a_svg(plano: dict[str, Any] | None, *, width: int = 520) -> str:
    """Genera SVG autocontenido a partir de la estructura `plano` de la ficha."""
    if not plano:
        return ""
    cols: list[str] = list(plano.get("cols") or [])
    rows: list[str] = list(plano.get("rows") or [])  # arriba → abajo
    if not cols or not rows:
        return ""

    nodos: dict[str, str] = dict(plano.get("nodos") or {})
    vacios: set[str] = {str(v) for v in (plano.get("vacios") or [])}
    # Intersecciones sin estructura: también las marcadas void en celdas legado
    for k, v in (plano.get("celdas") or {}).items():
        if v == "void":
            vacios.add(str(k))

    # Si no hay nodos explícitos, todas las intersecciones no-vacías son columna
    if not nodos:
        for r in rows:
            for c in cols:
                key = f"{r}{c}"
                if key in vacios or c.upper() == "JUNTA":
                    continue
                nodos[key] = "col"

    # Completar nodos faltantes como col (salvo vacíos)
    for r in rows:
        for c in cols:
            key = f"{r}{c}"
            if key in vacios or c.upper() == "JUNTA":
                continue
            nodos.setdefault(key, "col")

    pad_l, pad_r, pad_t, pad_b = 48, 56, 52, 42
    n_c, n_r = len(cols), len(rows)
    # Espaciado uniforme
    usable_w = width - pad_l - pad_r
    step_x = usable_w / max(n_c - 1, 1) if n_c > 1 else usable_w / 2
    step_y = min(36.0, step_x * 0.85)
    height = int(pad_t + pad_b + step_y * max(n_r - 1, 1) + 8)
    if n_r == 1:
        height = pad_t + pad_b + 40

    def xy(ci: int, ri: int) -> tuple[float, float]:
        x = pad_l + ci * step_x
        y = pad_t + ri * step_y
        return x, y

    col_i = {c: i for i, c in enumerate(cols)}
    row_i = {r: i for i, r in enumerate(rows)}

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Plano de inspección">'
        f"<rect width='100%' height='100%' fill='#ffffff'/>"
    ]

    titulo = plano.get("titulo") or ""
    if titulo:
        parts.append(
            f'<text x="{width/2}" y="18" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="13" '
            f'font-weight="700" fill="#00247D">{escape(titulo)}</text>'
        )

    orient = plano.get("orientacion") or {}
    if orient:
        # Arriba / abajo / izq / der en rojo
        if orient.get("arriba"):
            parts.append(
                f'<text x="{width/2}" y="{pad_t - 18}" text-anchor="middle" '
                f'font-family="Arial,Helvetica,sans-serif" font-size="10" '
                f'font-weight="700" fill="#cf142b">{escape(orient["arriba"])}</text>'
            )
        if orient.get("abajo"):
            parts.append(
                f'<text x="{width/2}" y="{height - 10}" text-anchor="middle" '
                f'font-family="Arial,Helvetica,sans-serif" font-size="10" '
                f'font-weight="700" fill="#cf142b">{escape(orient["abajo"])}</text>'
            )
        if orient.get("izq"):
            parts.append(
                f'<text x="12" y="{pad_t + step_y * (n_r - 1) / 2}" '
                f'text-anchor="middle" transform="rotate(-90 12,'
                f'{pad_t + step_y * (n_r - 1) / 2})" '
                f'font-family="Arial,Helvetica,sans-serif" font-size="10" '
                f'font-weight="700" fill="#cf142b">{escape(orient["izq"])}</text>'
            )
        if orient.get("der"):
            parts.append(
                f'<text x="{width - 14}" y="{pad_t + step_y * (n_r - 1) / 2}" '
                f'text-anchor="middle" transform="rotate(90 {width - 14},'
                f'{pad_t + step_y * (n_r - 1) / 2})" '
                f'font-family="Arial,Helvetica,sans-serif" font-size="10" '
                f'font-weight="700" fill="#cf142b">{escape(orient["der"])}</text>'
            )

    # Líneas de eje (discontinuas)
    x0, _ = xy(0, 0)
    x1, _ = xy(n_c - 1, 0)
    _, y0 = xy(0, 0)
    _, y1 = xy(0, n_r - 1)
    for ci, c in enumerate(cols):
        x, _ = xy(ci, 0)
        if str(c).upper() == "JUNTA":
            continue
        parts.append(
            f'<line x1="{x}" y1="{y0 - 8}" x2="{x}" y2="{y1 + 8}" '
            f'stroke="#64748b" stroke-width="1" stroke-dasharray="4 3"/>'
        )
    for ri, r in enumerate(rows):
        _, y = xy(0, ri)
        parts.append(
            f'<line x1="{x0 - 8}" y1="{y}" x2="{x1 + 8}" y2="{y}" '
            f'stroke="#64748b" stroke-width="1" stroke-dasharray="4 3"/>'
        )

    # Burbujas de ejes
    def bubble(cx: float, cy: float, label: str) -> None:
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="9" fill="#fce7f3" '
            f'stroke="#db2777" stroke-width="1.5"/>'
            f'<text x="{cx}" y="{cy + 3.5}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="9" '
            f'font-weight="700" fill="#9d174d">{escape(label)}</text>'
        )

    for ci, c in enumerate(cols):
        if str(c).upper() == "JUNTA":
            continue
        x, _ = xy(ci, 0)
        bubble(x, y0 - 22, c)
        bubble(x, y1 + 22, c)
    for ri, r in enumerate(rows):
        _, y = xy(0, ri)
        bubble(x0 - 22, y, r)
        bubble(x1 + 22, y, r)

    # Franja junta (si hay columna JUNTA)
    if any(str(c).upper() == "JUNTA" for c in cols):
        ji = next(i for i, c in enumerate(cols) if str(c).upper() == "JUNTA")
        jx, _ = xy(ji, 0)
        # mitad entre vecinos
        left = xy(ji - 1, 0)[0] if ji > 0 else jx - step_x / 2
        right = xy(ji + 1, 0)[0] if ji < n_c - 1 else jx + step_x / 2
        mid = (left + right) / 2
        w = max(10, (right - left) * 0.35)
        parts.append(
            f'<rect x="{mid - w/2}" y="{y0 - 6}" width="{w}" height="{y1 - y0 + 12}" '
            f'fill="#fde68a" stroke="#ca8a04" stroke-width="1" opacity="0.85"/>'
        )
        parts.append(
            f'<text x="{mid}" y="{(y0+y1)/2}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="8" '
            f'font-weight="700" fill="#92400e" '
            f'transform="rotate(-90 {mid},{(y0+y1)/2})">JUNTA</text>'
        )

    # Tramos (rectángulos entre nudos)
    for tr in plano.get("tramos") or []:
        fila = str(tr.get("fila") or "")
        de = str(tr.get("de") or "")
        a = str(tr.get("a") or "")
        nivel = str(tr.get("nivel") or "bc")
        if fila not in row_i or de not in col_i or a not in col_i:
            continue
        stroke, fill = _nivel_stroke(nivel)
        x_a, y = xy(col_i[de], row_i[fila])
        x_b, _ = xy(col_i[a], row_i[fila])
        if x_b < x_a:
            x_a, x_b = x_b, x_a
        pad = 10
        parts.append(
            f'<rect x="{x_a + pad}" y="{y - 7}" width="{max(8, x_b - x_a - 2*pad)}" '
            f'height="14" fill="{fill}" fill-opacity="0.35" stroke="{stroke}" '
            f'stroke-width="2" rx="2"/>'
        )

    # Tramos verticales (opcional: eje + entre filas)
    for tr in plano.get("tramos_vert") or []:
        eje = str(tr.get("eje") or "")
        de = str(tr.get("de") or "")
        a = str(tr.get("a") or "")
        nivel = str(tr.get("nivel") or "bc")
        if eje not in col_i or de not in row_i or a not in row_i:
            continue
        stroke, fill = _nivel_stroke(nivel)
        x, y_a = xy(col_i[eje], row_i[de])
        _, y_b = xy(col_i[eje], row_i[a])
        if y_b < y_a:
            y_a, y_b = y_b, y_a
        pad = 10
        parts.append(
            f'<rect x="{x - 7}" y="{y_a + pad}" width="14" '
            f'height="{max(8, y_b - y_a - 2*pad)}" fill="{fill}" fill-opacity="0.35" '
            f'stroke="{stroke}" stroke-width="2" rx="2"/>'
        )

    # Flechas
    for fl in plano.get("flechas") or []:
        eje = str(fl.get("eje") or "")
        entre = fl.get("entre") or ()
        if len(entre) != 2 or eje not in col_i:
            continue
        r0, r1 = str(entre[0]), str(entre[1])
        if r0 not in row_i or r1 not in row_i:
            continue
        x, y0f = xy(col_i[eje], row_i[r0])
        _, y1f = xy(col_i[eje], row_i[r1])
        cy = (y0f + y1f) / 2
        label = escape(str(fl.get("label") or "Flecha"))
        tw = max(42, 7 * len(label) + 12)
        parts.append(
            f'<rect x="{x - tw/2}" y="{cy - 9}" width="{tw}" height="18" '
            f'fill="#fbcfe8" stroke="#db2777" stroke-width="1.5" rx="3"/>'
            f'<text x="{x}" y="{cy + 4}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="9" '
            f'font-weight="700" fill="#9d174d">{label}</text>'
        )

    # Nodos (columnas)
    for key, tipo in nodos.items():
        # key = fila+col e.g. 7A or T2-A with row 2 → need parse carefully
        # Convención: fila es prefijo que coincide con un row, resto es col
        ri = ci = None
        for r in sorted(rows, key=len, reverse=True):
            if key.startswith(r):
                rest = key[len(r) :]
                if rest in col_i:
                    ri, ci = row_i[r], col_i[rest]
                    break
        if ri is None or ci is None:
            continue
        if key in vacios:
            continue
        x, y = xy(ci, ri)
        # cuadrado azul
        s = 8
        parts.append(
            f'<rect x="{x - s/2}" y="{y - s/2}" width="{s}" height="{s}" '
            f'fill="#3b82f6" stroke="#1e40af" stroke-width="0.8"/>'
        )
        t = (tipo or "col").lower()
        if t in ("col_a", "a"):
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="12" fill="none" '
                f'stroke="#eab308" stroke-width="2.2"/>'
            )
        elif t in ("col_bc", "bc", "dmg", "b", "c"):
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="12" fill="none" '
                f'stroke="#dc2626" stroke-width="2.2"/>'
            )
        elif t == "aux":
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="12" fill="none" '
                f'stroke="#a855f7" stroke-width="1.5" stroke-dasharray="3 2"/>'
            )

    # Entrada
    entrada = plano.get("entrada")
    if entrada and isinstance(entrada, str):
        # cerca del nudo indicado
        for r in sorted(rows, key=len, reverse=True):
            if entrada.startswith(r):
                rest = entrada[len(r) :]
                if rest in col_i:
                    x, y = xy(col_i[rest], row_i[r])
                    parts.append(
                        f'<text x="{x + 16}" y="{y + 18}" '
                        f'font-family="Arial,Helvetica,sans-serif" font-size="9" '
                        f'fill="#1a2332">Entrada</text>'
                    )
                    break

    nota = plano.get("nota_pie") or ""
    if nota:
        parts.append(
            f'<text x="{pad_l}" y="{height - 4}" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="8" '
            f'fill="#64748b">{escape(nota)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def enriquecer_plano(ej: dict[str, Any]) -> dict[str, Any]:
    """Adjunta svg_html a un ejemplo o al mini_ejemplo del mapa de estilo."""
    out = dict(ej)
    plano = ej.get("plano")
    if plano:
        out["svg_html"] = plano_a_svg(plano)
        out["nota_pie"] = plano.get("nota_pie") or ej.get("nota_pie") or ""
    return out
