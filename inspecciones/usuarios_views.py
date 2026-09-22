"""Panel de gestión de usuarios — solo administradores."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from inspecciones.models import EquipoBrigada
from inspecciones.usuarios_gestion import (
    ROLES_ALTA,
    crear_usuario_operativo,
    emitir_clave,
    listar_usuarios_gestion,
    proponer_username,
    set_activo,
)
from inspecciones.workflow import es_administrador


def _solo_admin(request):
    if not es_administrador(request.user):
        return HttpResponseForbidden(
            "Solo administradores pueden gestionar usuarios y claves."
        )
    return None


@staff_member_required
@require_http_methods(["GET", "POST"])
def gestion_usuarios(request):
    denied = _solo_admin(request)
    if denied:
        return denied

    preview_username = ""
    if request.method == "GET" and request.GET.get("preview"):
        try:
            eq = request.GET.get("equipo") or None
            equipo = int(eq) if eq else None
            preview_username = proponer_username(request.GET.get("rol") or "", equipo)
        except (ValueError, TypeError):
            preview_username = ""

    if request.method == "POST":
        action = request.POST.get("action", "crear")
        try:
            if action == "crear":
                eq_raw = (request.POST.get("equipo") or "").strip()
                equipo = int(eq_raw) if eq_raw else None
                result = crear_usuario_operativo(
                    rol=request.POST.get("rol") or "",
                    first_name=request.POST.get("first_name") or "",
                    last_name=request.POST.get("last_name") or "",
                    equipo=equipo,
                    username=(request.POST.get("username") or "").strip() or None,
                    por=request.user,
                )
                messages.success(
                    request,
                    f"Usuario creado: {result['username']} · clave {result['password']}",
                )
                request.session["ultima_clave_creada"] = {
                    "username": result["username"],
                    "password": result["password"],
                    "rol": result["rol"],
                }
            elif action == "regenerar":
                uid = int(request.POST.get("user_id", "0"))
                target = get_object_or_404(User, pk=uid, is_staff=True)
                if target.is_superuser and target.pk != request.user.pk:
                    messages.error(
                        request,
                        "No regenere la clave de otro administrador desde aquí.",
                    )
                else:
                    pwd = emitir_clave(target, por=request.user)
                    messages.success(
                        request,
                        f"Nueva clave para {target.username}: {pwd}",
                    )
                    request.session["ultima_clave_creada"] = {
                        "username": target.username,
                        "password": pwd,
                        "rol": "regenerada",
                    }
            elif action == "activar":
                uid = int(request.POST.get("user_id", "0"))
                target = get_object_or_404(User, pk=uid, is_staff=True)
                set_activo(target, True)
                messages.success(request, f"Activado: {target.username}")
            elif action == "desactivar":
                uid = int(request.POST.get("user_id", "0"))
                target = get_object_or_404(User, pk=uid, is_staff=True)
                set_activo(target, False)
                messages.success(request, f"Desactivado: {target.username}")
            else:
                messages.error(request, "Acción no reconocida.")
        except ValueError as exc:
            messages.error(request, str(exc))
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Error: {exc}")
        return HttpResponseRedirect(reverse("gestion_usuarios"))

    ultima = request.session.pop("ultima_clave_creada", None)
    equipos = list(
        EquipoBrigada.objects.filter(activo=True).order_by("numero").values("numero", "nombre")
    )
    if not equipos:
        equipos = [{"numero": n, "nombre": f"Equipo {n}"} for n in range(1, 9)]

    return render(
        request,
        "inspecciones/gestion_usuarios.html",
        {
            "title": "Gestión de usuarios",
            "filas": listar_usuarios_gestion(),
            "roles_alta": ROLES_ALTA,
            "equipos": equipos,
            "preview_username": preview_username,
            "ultima_clave": ultima,
        },
    )
