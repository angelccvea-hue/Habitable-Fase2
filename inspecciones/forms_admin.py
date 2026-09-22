"""Formulario admin CasoRojo — selección tipada de procedimientos del catálogo."""
from __future__ import annotations

import re

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError

from inspecciones.catalogo_procedimientos import asegurar_procedimientos_catalogo, listar_procedimientos_ayuda
from inspecciones.field_hints import FIELD_HINTS, hint_for
from inspecciones.models import CasoRojo
from inspecciones.proc_metrado_sync import metrado_snapshot_for_caso
from inspecciones.widgets_procedimientos import ProcedimientosCatalogoTableWidget


def _parse_codigos(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,;\n]+", raw)
    return [p.strip().upper() for p in parts if p.strip()]


def apply_field_hints(form: forms.BaseForm) -> None:
    """Asigna help_text corto a cada campo visible del formulario."""
    for name, field in form.fields.items():
        text = hint_for(name, getattr(field, "help_text", "") or "")
        if text:
            field.help_text = text


class CasoRojoAdminForm(forms.ModelForm):
    """Tabla Sí/No del catálogo (estilo Excel) + texto libre opcional en proc_codigos."""

    procedimientos_catalogo = forms.MultipleChoiceField(
        required=False,
        label="Procedimientos del catálogo (marque Sí como en Excel)",
        widget=ProcedimientosCatalogoTableWidget(),
        help_text=FIELD_HINTS["procedimientos_catalogo"],
    )

    class Meta:
        model = CasoRojo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            asegurar_procedimientos_catalogo()
        except Exception:
            pass
        rows = listar_procedimientos_ayuda()
        choices = [
            (r["codigo"], f"{r['codigo']} — {r['titulo']} ({r['categoria']})")
            for r in rows
        ]
        metrado_by_code = metrado_snapshot_for_caso(self.instance)
        self.fields["procedimientos_catalogo"].choices = choices
        self.fields["procedimientos_catalogo"].widget = ProcedimientosCatalogoTableWidget(
            rows=rows,
            metrado_by_code=metrado_by_code,
        )
        self.fields["procedimientos_catalogo"].widget.choices = choices
        initial_codes = set()
        if self.instance and self.instance.pk:
            initial_codes = set(_parse_codigos(self.instance.proc_codigos or ""))
        catalog_set = {c[0] for c in choices}
        self.fields["procedimientos_catalogo"].initial = sorted(
            initial_codes & catalog_set
        )
        self._proc_catalog_rows = rows
        apply_field_hints(self)
        if "proc_codigos" in self.fields:
            self.fields["proc_codigos"].widget.attrs.setdefault("rows", 2)
            self.fields["proc_codigos"].help_text = (
                "Se llena con los Sí de la tabla. Puede añadir códigos extra "
                "separados por coma si no están en el catálogo."
            )

    def clean(self):
        cleaned = super().clean()
        selected = list(cleaned.get("procedimientos_catalogo") or [])
        # Si llenó metrados sin marcar Sí, incluir el código automáticamente
        from inspecciones.proc_metrado_sync import _has_metrado_data, read_proc_metrado_from_post

        catalog_codes = {c for c, _ in self.fields["procedimientos_catalogo"].choices}
        if self.data is not None:
            posted = read_proc_metrado_from_post(self.data, sorted(catalog_codes))
            for code, vals in posted.items():
                if _has_metrado_data(vals) and code not in selected:
                    selected.append(code)
            cleaned["procedimientos_catalogo"] = selected
        typed = _parse_codigos(cleaned.get("proc_codigos") or "")
        extras = [c for c in typed if c not in catalog_codes]
        merged = []
        seen = set()
        for c in selected + extras:
            if c not in seen:
                merged.append(c)
                seen.add(c)
        cleaned["proc_codigos"] = ", ".join(merged)

        if self.errors:
            return cleaned

        from inspecciones import choices as ch
        from inspecciones.workflow import validar_dictamen

        skip = {"procedimientos_catalogo"}
        for name, value in cleaned.items():
            if name in skip or not hasattr(self.instance, name):
                continue
            try:
                setattr(self.instance, name, value)
            except (TypeError, ValueError):
                continue
        estado = cleaned.get("estado_2da") or self.instance.estado_2da or ""
        cerrar = estado in (
            ch.Estado2daRonda.PENDIENTE_REVISION,
            ch.Estado2daRonda.REVISADO,
            ch.Estado2daRonda.APROBADO,
            ch.Estado2daRonda.PUBLICADO,
        )
        try:
            self.instance.aplicar_correcciones_a_precarga()
            validar_dictamen(self.instance, cerrar=cerrar)
        except DjangoValidationError as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise forms.ValidationError(list(msgs)) from exc
        return cleaned
