"""Vistas del tablero de asignación (admin + coordinadores; revisores no)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from inspecciones.asignacion import (
    aplicar_asignacion,
    filtrar_casos,
    kpis_asignacion,
    opciones_usuario_select,
    resumen_usuarios,
    resumen_usuarios_por_equipo,
    usuarios_por_rol,
    etiqueta_usuario_ui,
)
from inspecciones.models import CasoRojo
from inspecciones.workflow import es_administrador, filtrar_casos_por_rol, puede_asignar_casos


def _requiere_asignador(request):
    if not puede_asignar_casos(request.user):
        return HttpResponseForbidden(
            "Solo administradores y coordinadores pueden asignar casos. "
            "Los revisores ven el inventario pero no asignan."
        )
    return None


@staff_member_required
@require_http_methods(["GET", "POST"])
def tablero_asignacion(request):
    denied = _requiere_asignador(request)
    if denied:
        return denied

    if request.method == "POST":
        return _procesar_asignacion(request)

    qs = filtrar_casos(request)
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page"))

    base_qs = filtrar_casos_por_rol(request.user)
    estados = (
        base_qs.exclude(estado_2da="")
        .values_list("estado_2da", flat=True)
        .distinct()
        .order_by("estado_2da")
    )
    bandas = (
        base_qs.exclude(banda="")
        .values_list("banda", flat=True)
        .distinct()
        .order_by("banda")
    )

    usuarios = usuarios_por_rol(request.user)
    es_admin = es_administrador(request.user)
    # Etiquetas en celdas de casos asignados
    for caso in page.object_list:
        for attr in ("coordinador_asignado", "inspector_asignado", "revisor_asignado"):
            u = getattr(caso, attr, None)
            if u:
                ui = etiqueta_usuario_ui(
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                )
                setattr(caso, f"{attr}_label", ui["etiqueta_corta"] if ui["equipo"] else ui["nombre"])
                setattr(caso, f"{attr}_equipo", ui["equipo"])
            else:
                setattr(caso, f"{attr}_label", "")
                setattr(caso, f"{attr}_equipo", "")

    ctx = {
        "kpis": kpis_asignacion(request.user),
        "usuarios_tabla": resumen_usuarios(request.user),
        "usuarios_por_equipo": resumen_usuarios_por_equipo(request.user),
        "inspectores": opciones_usuario_select(usuarios["inspectores"]),
        "revisores": opciones_usuario_select(usuarios["revisores"]),
        "coordinadores": opciones_usuario_select(usuarios["coordinadores"]),
        "casos": page,
        "paginator": paginator,
        "estados": estados,
        "bandas": bandas,
        "filtros": request.GET,
        "total_filtrado": paginator.count,
        "es_admin": es_admin,
        "rol_etiqueta": "Administrador" if es_admin else "Coordinador",
        "carga_titulo": (
            "Carga por usuario (todos los equipos)"
            if es_admin
            else "Carga de mi equipo (bolsa propia)"
        ),
    }
    return render(request, "inspecciones/tablero_asignacion.html", ctx)


def _procesar_asignacion(request):
    action = request.POST.get("action", "masiva")
    redirect_url = reverse("tablero_asignacion") + "?" + request.POST.get("query_string", "")
    es_admin = es_administrador(request.user)

    if action == "uno":
        try:
            caso_id = int(request.POST.get("caso_id", ""))
        except ValueError:
            messages.error(request, "Caso inválido.")
            return redirect(redirect_url)
        casos = CasoRojo.objects.filter(pk=caso_id)
    else:
        ids = [int(x) for x in request.POST.getlist("caso_ids") if x.isdigit()]
        if not ids:
            messages.warning(request, "Seleccione al menos un caso.")
            return redirect(redirect_url)
        casos = CasoRojo.objects.filter(pk__in=ids)

    if not es_admin:
        casos = casos.filter(coordinador_asignado=request.user)

    coord_raw = request.POST.get("coordinador_id", "")
    inspector_raw = request.POST.get("inspector_id", "")
    # Revisor: bandeja compartida — no se asigna desde este tablero.

    limpiar_coord = coord_raw == "__clear__"
    limpiar_inspector = inspector_raw == "__clear__"

    coordinador_id = None if limpiar_coord or not coord_raw else int(coord_raw)
    inspector_id = None if limpiar_inspector or not inspector_raw else int(inspector_raw)

    if not es_admin:
        coordinador_id = None
        limpiar_coord = False

    if not any([coordinador_id, inspector_id, limpiar_coord, limpiar_inspector]):
        messages.warning(
            request,
            "Indique coordinador o inspector a asignar/quitar. "
            "Los revisores no se asignan: usan la bandeja Por revisión.",
        )
        return redirect(redirect_url)

    n = aplicar_asignacion(
        casos,
        user=request.user,
        coordinador_id=coordinador_id,
        inspector_id=inspector_id,
        revisor_id=None,
        limpiar_coordinador=limpiar_coord,
        limpiar_inspector=limpiar_inspector,
        limpiar_revisor=False,
    )
    messages.success(request, f"Asignación aplicada a {n} caso(s).")
    return redirect(redirect_url)
