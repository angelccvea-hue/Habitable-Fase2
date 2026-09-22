# -*- coding: utf-8 -*-
"""Sincroniza columnas tipo Excel (ubicación…nota) del catálogo de procedimientos → LineaMetrado."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from inspecciones import choices as ch

_ELEMENTO_POR_CAT = {
    "COL": ch.ElementoMetrado.COLUMNA,
    "MAM": ch.ElementoMetrado.MURO,
    "VIG": ch.ElementoMetrado.VIGA,
}

_FIELDS = (
    "ubicacion",
    "cantidad",
    "unidad",
    "severidad",
    "accion",
    "confianza",
    "nota",
)


def _post_key(codigo: str, field: str) -> str:
    return f"proc_m_{codigo}__{field}"


def metrado_snapshot_for_caso(caso) -> dict[str, dict[str, Any]]:
    """Primera línea por codigo_partida (mayúsculas) → dict de campos editables."""
    out: dict[str, dict[str, Any]] = {}
    if not caso or not getattr(caso, "pk", None):
        return out
    qs = caso.lineas_metrado.order_by("orden", "id")
    for ln in qs:
        code = (ln.codigo_partida or "").strip().upper()
        if not code or code in out:
            continue
        out[code] = {
            "ubicacion": ln.ubicacion or "",
            "cantidad": "" if ln.cantidad is None else str(ln.cantidad).rstrip("0").rstrip("."),
            "unidad": ln.unidad or "",
            "severidad": ln.severidad or "",
            "accion": ln.accion or "",
            "confianza": ln.confianza or "",
            "nota": ln.nota or "",
            "pk": ln.pk,
        }
    return out


def _parse_cantidad(raw: str):
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _has_metrado_data(vals: dict[str, str]) -> bool:
    for k in _FIELDS:
        v = (vals.get(k) or "").strip()
        if not v or v == "Pendiente":
            continue
        return True
    return False


def read_proc_metrado_from_post(post, codigos: list[str]) -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = {}
    for codigo in codigos:
        row = {}
        for f in _FIELDS:
            row[f] = (post.get(_post_key(codigo, f)) or "").strip()
        data[codigo] = row
    return data


def sync_procedimientos_metrados(caso, post, selected_codes: list[str], catalog_rows: list[dict]) -> int:
    """
    Upsert LineaMetrado para códigos con Sí o con datos de metrado llenos.
    Devuelve cuántas líneas se crearon/actualizaron.
    """
    from inspecciones.models import LineaMetrado

    if not caso or not caso.pk:
        return 0

    selected = {str(c).strip().upper() for c in (selected_codes or []) if str(c).strip()}
    by_cat = {
        (r.get("codigo") or "").upper(): (r.get("categoria") or "").upper()
        for r in (catalog_rows or [])
    }
    all_codes = sorted(set(by_cat) | selected)
    posted = read_proc_metrado_from_post(post, all_codes)

    existing = {
        (ln.codigo_partida or "").strip().upper(): ln
        for ln in caso.lineas_metrado.order_by("orden", "id")
        if (ln.codigo_partida or "").strip()
    }
    # Solo primera ocurrencia por código
    first_by_code: dict[str, Any] = {}
    for code, ln in existing.items():
        if code not in first_by_code:
            first_by_code[code] = ln

    max_orden = caso.lineas_metrado.order_by("-orden").values_list("orden", flat=True).first() or 0
    n = 0
    for codigo in all_codes:
        vals = posted.get(codigo) or {}
        checked = codigo in selected
        if not checked and not _has_metrado_data(vals):
            continue
        if not _has_metrado_data(vals) and checked:
            # Solo Sí sin cantidades → no crea línea vacía (queda en proc_codigos)
            continue

        cat = by_cat.get(codigo, "")
        elemento = _ELEMENTO_POR_CAT.get(cat, ch.ElementoMetrado.PENDIENTE)
        cantidad = _parse_cantidad(vals.get("cantidad", ""))
        unidad = vals.get("unidad") or ch.UnidadMetrado.PENDIENTE
        severidad = vals.get("severidad") or ch.NivelABC.PENDIENTE
        accion = vals.get("accion") or ch.AccionMetrado.PENDIENTE
        confianza = vals.get("confianza") or ch.ConfianzaMetrado.PENDIENTE
        ubicacion = vals.get("ubicacion") or ""
        nota = vals.get("nota") or ""

        ln = first_by_code.get(codigo)
        if ln is None:
            max_orden += 1
            ln = LineaMetrado(
                caso=caso,
                orden=max_orden,
                codigo_partida=codigo,
            )
            first_by_code[codigo] = ln

        ln.codigo_partida = codigo
        ln.ubicacion = ubicacion[:128]
        ln.cantidad = cantidad
        ln.unidad = unidad[:16]
        ln.severidad = severidad[:16]
        ln.accion = accion[:32]
        ln.confianza = confianza[:16]
        ln.nota = nota[:500]
        if not ln.elemento or ln.elemento == ch.ElementoMetrado.PENDIENTE:
            ln.elemento = elemento
        ln.save()
        n += 1
    return n
