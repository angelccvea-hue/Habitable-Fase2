# -*- coding: utf-8 -*-
"""Widget de catálogo de procedimientos estilo pestaña Excel (Sí + metrados)."""
from __future__ import annotations

from django.forms.widgets import CheckboxSelectMultiple

from inspecciones import choices as ch


def _choice_list(enum_cls) -> list[tuple[str, str]]:
    return [(c.value, c.label) for c in enum_cls]


class ProcedimientosCatalogoTableWidget(CheckboxSelectMultiple):
    """Tabla por categoría con Sí + columnas tipo hoja Metrados del Excel."""

    template_name = "inspecciones/widgets/procedimientos_catalogo_table.html"
    option_template_name = "django/forms/widgets/checkbox_option.html"

    def __init__(
        self,
        attrs=None,
        choices=(),
        *,
        rows: list[dict] | None = None,
        metrado_by_code: dict | None = None,
    ):
        super().__init__(attrs, choices)
        self.rows = list(rows or [])
        self.metrado_by_code = dict(metrado_by_code or {})

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        selected = set()
        if value:
            selected = {str(v) for v in value}
        order = ("COL", "MAM", "VIG")
        groups: dict[str, list[dict]] = {k: [] for k in order}
        other: list[dict] = []
        for r in self.rows:
            cat = (r.get("categoria") or "").upper() or "OTRO"
            code = r["codigo"]
            m = self.metrado_by_code.get(code.upper()) or self.metrado_by_code.get(code) or {}
            item = {
                "codigo": code,
                "categoria": cat,
                "titulo": r.get("titulo") or "",
                "checked": code in selected or code.upper() in selected,
                "ubicacion": m.get("ubicacion", ""),
                "cantidad": m.get("cantidad", ""),
                "unidad": m.get("unidad") or ch.UnidadMetrado.PENDIENTE,
                "severidad": m.get("severidad") or ch.NivelABC.PENDIENTE,
                "accion": m.get("accion") or ch.AccionMetrado.PENDIENTE,
                "confianza": m.get("confianza") or ch.ConfianzaMetrado.PENDIENTE,
                "nota": m.get("nota", ""),
            }
            if cat in groups:
                groups[cat].append(item)
            else:
                other.append(item)
        sections = []
        labels = {
            "COL": "Columnas (COL)",
            "MAM": "Mampostería (MAM)",
            "VIG": "Vigas (VIG)",
        }
        for cat in order:
            if groups[cat]:
                sections.append(
                    {"key": cat, "label": labels.get(cat, cat), "items": groups[cat]}
                )
        if other:
            sections.append({"key": "OTRO", "label": "Otros", "items": other})
        context["widget"]["sections"] = sections
        context["widget"]["name"] = name
        context["widget"]["choices_unidad"] = _choice_list(ch.UnidadMetrado)
        context["widget"]["choices_severidad"] = _choice_list(ch.NivelABC)
        context["widget"]["choices_accion"] = _choice_list(ch.AccionMetrado)
        context["widget"]["choices_confianza"] = _choice_list(ch.ConfianzaMetrado)
        return context

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        return super().create_option(name, value, label, selected, index, subindex, attrs)
