"""Carga de Excel de informe (inspectores / coordinadores) y descarga de croquis."""
from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from inspecciones.excel_import import ExcelImportError, import_excel_bytes
from inspecciones.models import CasoRojo, CroquisAdjunto
from inspecciones.workflow import (
    es_coordinador,
    es_inspector,
    es_revisor,
    es_solo_consulta,
    usuario_puede_ver_caso,
    ve_todos_los_casos,
)

logger = logging.getLogger(__name__)


def _puede_cargar_excel(user) -> bool:
    if not user.is_authenticated or es_solo_consulta(user):
        return False
    return bool(
        user.is_superuser
        or es_coordinador(user)
        or es_inspector(user)
        or es_revisor(user)
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def cargar_excel_informe(request, pk: int | None = None):
    """
    Sube plantilla Excel llenada y actualiza el/los caso(s).
    Si pk está definido, restringe al caso de la ficha.
    """
    if not _puede_cargar_excel(request.user):
        messages.error(request, "No tiene permiso para cargar Excel.")
        return HttpResponseRedirect(reverse("admin:index"))

    caso = get_object_or_404(CasoRojo, pk=pk) if pk else None
    if caso and not usuario_puede_ver_caso(request.user, caso):
        messages.error(request, "No tiene acceso a este caso.")
        return HttpResponseRedirect(reverse("admin:index"))

    context = {
        "title": "Cargar Excel de informe",
        "caso": caso,
        "opts": CasoRojo._meta,
        "has_permission": True,
        "site_header": "CPEH — Habitable Fase II",
        "puede_overwrite_precarga": request.user.is_superuser or es_coordinador(request.user),
    }

    if request.method == "POST":
        archivo = request.FILES.get("archivo_excel")
        if not archivo:
            messages.error(request, "Seleccione un archivo .xlsx.")
            return render(request, "admin/inspecciones/cargar_excel.html", context)
        name = (archivo.name or "").lower()
        if not name.endswith((".xlsx", ".xlsm")):
            messages.error(request, "Solo se aceptan archivos Excel (.xlsx).")
            return render(request, "admin/inspecciones/cargar_excel.html", context)
        overwrite = request.POST.get("overwrite_precarga") == "1" and (
            request.user.is_superuser or es_coordinador(request.user)
        )
        try:
            result = import_excel_bytes(
                archivo.read(),
                caso_esperado=caso,
                overwrite_precarga=overwrite,
                user=request.user,
                solo_visibles_para=None if ve_todos_los_casos(request.user) else request.user,
            )
        except ExcelImportError as exc:
            logger.warning(
                "excel_import_fail user=%s caso_pk=%s file=%s err=%s",
                getattr(request.user, "username", "?"),
                getattr(caso, "pk", None),
                archivo.name,
                exc,
            )
            messages.error(request, str(exc))
            return render(request, "admin/inspecciones/cargar_excel.html", context)
        except Exception as exc:
            logger.exception(
                "excel_import_crash user=%s caso_pk=%s file=%s",
                getattr(request.user, "username", "?"),
                getattr(caso, "pk", None),
                archivo.name,
            )
            messages.error(
                request,
                f"Error inesperado al leer el Excel: {exc}. "
                "Pruebe de nuevo con la plantilla descargada del sistema.",
            )
            return render(request, "admin/inspecciones/cargar_excel.html", context)

        n = len(result["actualizados"])
        campos_tot = sum(len(r["campos"]) for r in result["actualizados"])
        messages.success(
            request,
            f"Excel aplicado: {n} caso(s), {campos_tot} campo(s) actualizado(s).",
        )
        for err in result.get("errores") or []:
            messages.warning(request, err)
        if caso:
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
            )
        if n == 1:
            return HttpResponseRedirect(
                reverse(
                    "admin:inspecciones_casorojo_change",
                    args=[result["actualizados"][0]["pk"]],
                )
            )
        return HttpResponseRedirect(reverse("admin:inspecciones_casorojo_changelist"))

    return render(request, "admin/inspecciones/cargar_excel.html", context)


@staff_member_required
@require_http_methods(["GET"])
def ver_croquis_adjunto(request, pk: int) -> FileResponse:
    doc = get_object_or_404(CroquisAdjunto, pk=pk)
    if not usuario_puede_ver_caso(request.user, doc.caso):
        return HttpResponseBadRequest("Sin permiso.")
    if not doc.archivo:
        return HttpResponseBadRequest("Sin archivo.")
    return FileResponse(
        doc.archivo.open("rb"),
        as_attachment=False,
        filename=doc.nombre_archivo_origen or doc.archivo.name,
    )
