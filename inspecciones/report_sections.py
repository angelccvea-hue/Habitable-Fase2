"""Secciones del informe PDF (mismos títulos numerados que el admin)."""
from __future__ import annotations

import re

from django.db import models

from inspecciones.catalogo_procedimientos import listar_procedimientos_ayuda
from inspecciones.models import CasoRojo
from inspecciones.section_labels import CASE_FIELDSETS


def _format_value(field: models.Field, value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(field, models.DateField):
        return value.strftime("%d/%m/%Y")
    if isinstance(field, models.DateTimeField):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value)


def _parse_codigos(raw: str) -> list[str]:
    if not raw:
        return []
    return [p.strip().upper() for p in re.split(r"[,;\n]+", raw) if p.strip()]


def _tabla_procedimientos_seleccionados(caso: CasoRojo) -> list[dict]:
    """Filas del catálogo marcadas Sí (para PDF tipo Excel)."""
    selected = set(_parse_codigos(caso.proc_codigos or ""))
    if not selected:
        return []
    by_code = {r["codigo"].upper(): r for r in listar_procedimientos_ayuda()}
    rows = []
    for code in _parse_codigos(caso.proc_codigos or ""):
        meta = by_code.get(code, {})
        rows.append(
            {
                "codigo": code,
                "categoria": meta.get("categoria") or "—",
                "titulo": meta.get("titulo") or "(código fuera de catálogo)",
                "seleccion": "Sí",
            }
        )
    return rows


def build_report_sections(caso: CasoRojo) -> list[dict]:
    sections: list[dict] = []
    for title, opts in CASE_FIELDSETS:
        if title.startswith("13 —"):
            continue
        rows = []
        for fname in opts["fields"]:
            # En PDF la selección tipada se muestra como tabla; no repetir CSV crudo.
            if fname == "proc_codigos":
                tabla_proc = _tabla_procedimientos_seleccionados(caso)
                if tabla_proc:
                    rows.append(
                        {
                            "label": "Procedimientos seleccionados (catálogo)",
                            "value": ", ".join(r["codigo"] for r in tabla_proc),
                            "es_tabla_proc": True,
                            "tabla_proc": tabla_proc,
                        }
                    )
                else:
                    rows.append(
                        {
                            "label": "Procedimientos seleccionados (catálogo)",
                            "value": "— (ningún código marcado Sí)",
                        }
                    )
                continue
            field = CasoRojo._meta.get_field(fname)
            rows.append(
                {
                    "label": str(field.verbose_name),
                    "value": _format_value(field, getattr(caso, fname)),
                }
            )
        if title.startswith("9 —"):
            lineas = list(
                caso.lineas_metrado.select_related("partida").order_by("orden", "id")
            )
            if lineas:
                rows.append(
                    {
                        "label": "Líneas de metrado",
                        "value": _format_lineas_metrado(lineas),
                        "es_tabla": True,
                        "tabla": [
                            {
                                "orden": ln.orden,
                                "codigo": ln.codigo_partida
                                or (ln.partida.codigo if ln.partida_id else ""),
                                "titulo": ln.partida.titulo if ln.partida_id else "",
                                "elemento": ln.elemento,
                                "id_pln01": getattr(ln, "id_pln01", "") or "",
                                "ubicacion": ln.ubicacion,
                                "cantidad": (
                                    f"{ln.cantidad:.3f}"
                                    if ln.cantidad is not None
                                    else ""
                                ),
                                "unidad": ln.unidad,
                                "severidad": ln.severidad,
                                "accion": ln.accion,
                                "confianza": ln.confianza,
                                "nota": ln.nota,
                                "costo": (
                                    str(ln.costo_estimado)
                                    if ln.costo_estimado is not None
                                    else ""
                                ),
                            }
                            for ln in lineas
                        ],
                    }
                )
            else:
                rows.append(
                    {
                        "label": "Líneas de metrado",
                        "value": "— (sin líneas capturadas)",
                    }
                )
        sections.append({"title": title, "rows": rows})
    return sections


def _format_lineas_metrado(lineas) -> str:
    parts = []
    for ln in lineas:
        cod = ln.codigo_partida or (ln.partida.codigo if ln.partida_id else "—")
        idp = (getattr(ln, "id_pln01", None) or "").strip()
        ubi = (ln.ubicacion or "").strip()
        where = idp or ubi or "—"
        cant = ln.cantidad if ln.cantidad is not None else "—"
        und = ln.unidad or ""
        parts.append(f"{cod} @ {where}: {cant} {und}".strip())
    return "; ".join(parts) if parts else "—"
