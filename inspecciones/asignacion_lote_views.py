# -*- coding: utf-8 -*-
"""Vista admin: carga Excel de IDs/certificados y asignación masiva a un equipo."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from inspecciones.asignacion import aplicar_asignacion, etiqueta_usuario_ui
from inspecciones.asignacion_lote_excel import (
    opciones_equipos_asignacion,
    parsear_excel_lote,
    plantilla_excel_bytes,
)
from inspecciones.models import CasoRojo
from inspecciones.workflow import es_administrador

SESSION_KEY = "asignacion_lote_pks"
SESSION_META = "asignacion_lote_meta"


def _requiere_admin(request):
    if not es_administrador(request.user):
        return HttpResponseForbidden(
            "Solo administradores pueden usar la carga masiva y asignación por equipo."
        )
    return None


@staff_member_required
@require_http_methods(["GET", "POST"])
def asignacion_lote_excel(request):
    denied = _requiere_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        action = request.POST.get("action", "upload")
        if action == "upload":
            return _post_upload(request)
        if action == "asignar":
            return _post_asignar(request)
        if action == "limpiar":
            request.session.pop(SESSION_KEY, None)
            request.session.pop(SESSION_META, None)
            messages.info(request, "Lote limpiado.")
            return redirect("asignacion_lote_excel")
        messages.error(request, "Acción no reconocida.")
        return redirect("asignacion_lote_excel")

    return _get_page(request)


@staff_member_required
@require_http_methods(["GET"])
def plantilla_asignacion_lote(request):
    denied = _requiere_admin(request)
    if denied:
        return denied
    data = plantilla_excel_bytes()
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = (
        'attachment; filename="plantilla_asignacion_lote_fase2.xlsx"'
    )
    return resp


def _get_page(request, preview: dict | None = None):
    pks = request.session.get(SESSION_KEY) or []
    meta = request.session.get(SESSION_META) or {}
    casos = []
    n_libres = 0
    n_ya = 0
    if pks:
        qs = (
            CasoRojo.objects.filter(pk__in=pks)
            .select_related("coordinador_asignado", "inspector_asignado")
            .order_by("-score", "hab_id")
        )
        by_pk = {c.pk: c for c in qs}
        for pk in pks:
            c = by_pk.get(pk)
            if not c:
                continue
            coord = c.coordinador_asignado
            equipo = ""
            ya = bool(coord)
            if coord:
                ui = etiqueta_usuario_ui(
                    username=coord.username,
                    first_name=coord.first_name,
                    last_name=coord.last_name,
                )
                equipo = ui.get("equipo") or coord.username
                n_ya += 1
            else:
                n_libres += 1
            casos.append(
                {
                    "pk": c.pk,
                    "hab_id": c.hab_id,
                    "certificado": c.certificado,
                    "nombre": c.nombre_conf or c.nombre_hab or "",
                    "banda": c.banda,
                    "estado_2da": c.estado_2da,
                    "score": c.score,
                    "equipo_actual": equipo,
                    "ya_asignado": ya,
                }
            )

    ctx = {
        "equipos": opciones_equipos_asignacion(),
        "preview": preview,
        "casos_lote": casos,
        "meta": meta,
        "n_lote": len(pks),
        "n_libres": n_libres,
        "n_ya_asignados": n_ya,
        "plantilla_url": reverse("plantilla_asignacion_lote"),
        "asignacion_url": reverse("tablero_asignacion"),
    }
    return render(request, "inspecciones/asignacion_lote_excel.html", ctx)


def _post_upload(request):
    f = request.FILES.get("archivo")
    if not f:
        messages.error(request, "Seleccione un archivo Excel (.xlsx).")
        return redirect("asignacion_lote_excel")
    name = (f.name or "").lower()
    if not (name.endswith(".xlsx") or name.endswith(".xlsm")):
        messages.error(request, "Formato no válido. Use .xlsx")
        return redirect("asignacion_lote_excel")
    content = f.read()
    if len(content) > 8 * 1024 * 1024:
        messages.error(request, "Archivo demasiado grande (máx. 8 MB).")
        return redirect("asignacion_lote_excel")

    result = parsear_excel_lote(content)
    if result.get("error"):
        messages.error(request, result["error"])
        return redirect("asignacion_lote_excel")

    pks = result["pks_ok"]
    request.session[SESSION_KEY] = pks
    request.session[SESSION_META] = {
        "archivo": f.name,
        "resumen": result["resumen"],
    }
    request.session.modified = True

    r = result["resumen"]
    msg = (
        f"Excel leído: {r.get('libres', 0)} libre(s) · "
        f"{r.get('ya_asignados', 0)} ya asignado(s) · "
        f"{r['no_encontrado']} no encontrados · "
        f"{r['vacio']} incompletos."
    )
    if r.get("ya_asignados"):
        messages.warning(
            request,
            msg + " Los ya asignados no se reasignarán (protección).",
        )
    else:
        messages.success(request, msg)
    return _get_page(request, preview=result)


def _post_asignar(request):
    pks = request.session.get(SESSION_KEY) or []
    if not pks:
        messages.warning(request, "No hay lote cargado. Suba un Excel primero.")
        return redirect("asignacion_lote_excel")

    selected = [int(x) for x in request.POST.getlist("caso_ids") if str(x).isdigit()]
    if selected:
        pks = [pk for pk in pks if pk in set(selected)]
    if not pks:
        messages.warning(request, "Seleccione al menos un caso del lote.")
        return redirect("asignacion_lote_excel")

    try:
        coordinador_id = int(request.POST.get("coordinador_id") or "")
    except ValueError:
        messages.error(request, "Seleccione un equipo / coordinador válido.")
        return redirect("asignacion_lote_excel")

    equipos = {e["coordinador_id"]: e for e in opciones_equipos_asignacion()}
    if coordinador_id not in equipos:
        messages.error(request, "El equipo elegido no está disponible.")
        return redirect("asignacion_lote_excel")

    forzar = request.POST.get("forzar_reasignacion") == "1"

    qs = CasoRojo.objects.filter(pk__in=pks).select_related("coordinador_asignado")
    libres = []
    ya_mismo = []
    ya_otro = []
    for c in qs:
        if c.coordinador_asignado_id is None:
            libres.append(c.pk)
        elif c.coordinador_asignado_id == coordinador_id:
            ya_mismo.append(c.pk)
        else:
            ya_otro.append(c.pk)

    if forzar:
        a_asignar = libres + ya_otro  # no tocar los que ya están en el mismo equipo
    else:
        a_asignar = libres
        if ya_otro or ya_mismo:
            messages.warning(
                request,
                f"Protección: se omitieron {len(ya_otro) + len(ya_mismo)} caso(s) "
                f"ya asignados ({len(ya_otro)} a otro equipo, {len(ya_mismo)} ya en el destino). "
                f"Marque «Forzar reasignación» solo si realmente desea mover los de otro equipo.",
            )

    if not a_asignar:
        messages.warning(
            request,
            "No hay casos libres para asignar. Todos los seleccionados ya tienen equipo.",
        )
        return redirect("asignacion_lote_excel")

    n = aplicar_asignacion(
        CasoRojo.objects.filter(pk__in=a_asignar),
        user=request.user,
        coordinador_id=coordinador_id,
    )
    eq = equipos[coordinador_id]
    messages.success(
        request,
        f"Asignados {n} caso(s) a {eq['etiqueta']} "
        f"({eq['coordinador_username']}).",
    )
    request.session.pop(SESSION_KEY, None)
    request.session.pop(SESSION_META, None)
    return redirect("asignacion_lote_excel")
