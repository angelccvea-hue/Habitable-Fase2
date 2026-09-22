# -*- coding: utf-8 -*-
"""Widgets de formulario para la ficha CasoRojo (admin)."""
from __future__ import annotations

from pathlib import PurePosixPath

from django.forms.widgets import ClearableFileInput


class CpehClearableFileInput(ClearableFileInput):
    """Nombre corto del archivo; sin checkbox limpiar (en inline se usa ¿Eliminar?)."""

    template_name = "django/forms/widgets/cpeh_clearable_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        display = ""
        if value and getattr(value, "name", None):
            display = PurePosixPath(str(value.name).replace("\\", "/")).name
        widget["display_name"] = display or ""
        return context
