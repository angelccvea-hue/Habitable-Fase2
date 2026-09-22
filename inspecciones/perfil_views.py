"""Perfil de usuario: nombre/apellido propios y edición por admin/coord."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from inspecciones.asignacion import equipo_de_username, etiqueta_equipo, usuarios_por_rol
from inspecciones.workflow import (
    es_administrador,
    es_solo_coordinador,
)


def _puede_editar_usuario(viewer: User, target: User) -> bool:
    if es_administrador(viewer):
        return True
    if viewer.pk == target.pk:
        return True
    if es_solo_coordinador(viewer):
        eq_self = equipo_de_username(viewer.username)
        eq_tgt = equipo_de_username(target.username)
        if eq_self and eq_tgt and eq_self == eq_tgt:
            return True
        # Coordinador puede editar revisores de su alcance (todos los revisores en lista)
        if target.groups.filter(name="cpeh_revisor").exists():
            return True
    return False


def _usuarios_editables(viewer: User) -> list[User]:
    if es_administrador(viewer):
        return list(
            User.objects.filter(is_active=True)
            .exclude(username__endswith=".demo")
            .order_by("username")
        )
    por = usuarios_por_rol(viewer)
    ids = set()
    for qs in por.values():
        ids.update(qs.values_list("pk", flat=True))
    ids.add(viewer.pk)
    return list(User.objects.filter(pk__in=ids, is_active=True).order_by("username"))


@staff_member_required
@require_http_methods(["GET", "POST"])
def mi_perfil(request):
    """Cada usuario edita su nombre y apellido."""
    user = request.user
    if request.method == "POST":
        first = (request.POST.get("first_name") or "").strip()[:150]
        last = (request.POST.get("last_name") or "").strip()[:150]
        user.first_name = first
        user.last_name = last
        user.save(update_fields=["first_name", "last_name"])
        messages.success(
            request,
            f"Perfil actualizado: {user.get_full_name() or user.username}.",
        )
        return HttpResponseRedirect(reverse("mi_perfil"))

    eq = equipo_de_username(user.username)
    return render(
        request,
        "inspecciones/mi_perfil.html",
        {
            "title": "Mi perfil",
            "perfil_user": user,
            "equipo_etiqueta": etiqueta_equipo(eq) if eq else "",
            "puede_gestionar_equipo": es_administrador(user) or es_solo_coordinador(user),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def gestionar_nombres_usuarios(request):
    """Admin / coordinador: nombre y apellido de usuarios de su alcance."""
    viewer = request.user
    if not (es_administrador(viewer) or es_solo_coordinador(viewer)):
        return HttpResponseForbidden(
            "Solo administrador o coordinador pueden editar nombres del equipo."
        )

    usuarios = _usuarios_editables(viewer)

    if request.method == "POST":
        n_ok = 0
        for u in usuarios:
            if not _puede_editar_usuario(viewer, u):
                continue
            first_key = f"first_{u.pk}"
            last_key = f"last_{u.pk}"
            if first_key not in request.POST and last_key not in request.POST:
                continue
            first = (request.POST.get(first_key) or "").strip()[:150]
            last = (request.POST.get(last_key) or "").strip()[:150]
            if u.first_name != first or u.last_name != last:
                u.first_name = first
                u.last_name = last
                u.save(update_fields=["first_name", "last_name"])
                n_ok += 1
        messages.success(request, f"Se actualizaron {n_ok} usuario(s).")
        return HttpResponseRedirect(reverse("gestionar_nombres"))

    filas = []
    for u in usuarios:
        eq = equipo_de_username(u.username)
        filas.append(
            {
                "user": u,
                "equipo": etiqueta_equipo(eq) if eq else "—",
            }
        )

    return render(
        request,
        "inspecciones/gestionar_nombres.html",
        {
            "title": "Nombres del equipo",
            "filas": filas,
        },
    )


@staff_member_required
@require_http_methods(["POST"])
def actualizar_nombre_usuario(request, pk: int):
    """Actualiza un solo usuario (formulario compacto)."""
    viewer = request.user
    target = get_object_or_404(User, pk=pk, is_active=True)
    if not _puede_editar_usuario(viewer, target):
        return HttpResponseForbidden("No puede editar este usuario.")
    target.first_name = (request.POST.get("first_name") or "").strip()[:150]
    target.last_name = (request.POST.get("last_name") or "").strip()[:150]
    target.save(update_fields=["first_name", "last_name"])
    messages.success(
        request,
        f"Actualizado {target.username}: {target.get_full_name() or '(sin nombre)'}.",
    )
    next_url = request.POST.get("next") or reverse("gestionar_nombres")
    return HttpResponseRedirect(next_url)
