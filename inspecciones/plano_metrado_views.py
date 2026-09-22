"""Visor multi-planta PLN-01 × catálogo MET-01."""
from __future__ import annotations

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import redirect_to_login
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from inspecciones import choices as ch
from inspecciones.models import CasoRojo, LineaMetrado, PartidaCatalogo, PlantaInspeccion
from inspecciones.partidas_catalogo import listar_partidas_ayuda
from inspecciones.workflow import usuario_puede_ver_caso

# Plantas de demostración cuando el caso aún no tiene PlantaInspeccion
_PLANTAS_DEMO = [
    {"codigo_piso": "PB", "titulo": "Planta baja", "orden": 1},
    {"codigo_piso": "P1", "titulo": "Piso 1", "orden": 2},
    {"codigo_piso": "P2", "titulo": "Piso 2", "orden": 3},
]


def _partidas_intervencion() -> list[dict]:
    rows = listar_partidas_ayuda()
    out = []
    for r in rows:
        g = str(r.get("grupo") or "")
        if "ESTUDIOS" in g.upper():
            continue
        out.append(r)
    return out


def _lineas_payload(caso: CasoRojo) -> list[dict]:
    out = []
    for ln in caso.lineas_metrado.select_related("partida").order_by("orden", "id"):
        out.append(
            {
                "id": ln.pk,
                "id_pln01": getattr(ln, "id_pln01", "") or "",
                "piso_pln": getattr(ln, "piso_pln", "") or "",
                "codigo_partida": ln.codigo_partida
                or (ln.partida.codigo if ln.partida_id else ""),
                "elemento": ln.elemento or "",
                "cantidad": float(ln.cantidad) if ln.cantidad is not None else None,
                "unidad": ln.unidad or "",
                "tipo_apuntamiento": getattr(ln, "tipo_apuntamiento", None) or "na",
                "nota": ln.nota or "",
                "ubicacion": ln.ubicacion or "",
                "titulo_partida": ln.partida.titulo if ln.partida_id else "",
            }
        )
    return out


def _plantas_payload(caso: CasoRojo | None) -> list[dict]:
    if caso is None:
        return list(_PLANTAS_DEMO)
    qs = caso.plantas_inspeccion.filter(activa=True).order_by("orden", "codigo_piso")
    rows = [
        {
            "id": p.pk,
            "codigo_piso": p.codigo_piso,
            "titulo": p.titulo or f"Planta {p.codigo_piso}",
            "orden": p.orden,
            "croquis_url": p.croquis.archivo.url if p.croquis_id and p.croquis.archivo else "",
        }
        for p in qs
    ]
    if rows:
        return rows
    # Fallback: pisos inferidos de metrados + croquis etiquetados
    pisos: dict[str, dict] = {}
    for ln in caso.lineas_metrado.all():
        p = (getattr(ln, "piso_pln", None) or "").strip().upper()
        if not p and (getattr(ln, "id_pln01", None) or "").strip():
            p = ln.id_pln01.strip().split("-", 1)[0].upper()
        if p and p not in pisos:
            pisos[p] = {
                "id": None,
                "codigo_piso": p,
                "titulo": f"Planta {p}",
                "orden": len(pisos) + 1,
                "croquis_url": "",
            }
    for cr in caso.croquis.all():
        p = (cr.codigo_piso or "").strip().upper()
        if not p:
            continue
        if p not in pisos:
            pisos[p] = {
                "id": None,
                "codigo_piso": p,
                "titulo": cr.titulo or f"Planta {p}",
                "orden": len(pisos) + 1,
                "croquis_url": cr.archivo.url if cr.archivo else "",
            }
        elif cr.archivo and not pisos[p]["croquis_url"]:
            pisos[p]["croquis_url"] = cr.archivo.url
    if pisos:
        return sorted(pisos.values(), key=lambda x: (x["orden"], x["codigo_piso"]))
    return list(_PLANTAS_DEMO)


@ensure_csrf_cookie
@require_GET
def visor_plano_metrado(request, pk: int | None = None):
    caso = None
    lineas: list[dict] = []
    if pk is not None:
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect_to_login(request.get_full_path())
        caso = get_object_or_404(CasoRojo, pk=pk)
        if not usuario_puede_ver_caso(request.user, caso):
            return JsonResponse({"error": "Sin permiso"}, status=403)
        lineas = _lineas_payload(caso)
    elif not settings.DEBUG:
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect_to_login(request.get_full_path())

    plantas = _plantas_payload(caso)
    ctx = {
        "caso": caso,
        "partidas_json": json.dumps(
            _partidas_intervencion(), cls=DjangoJSONEncoder, ensure_ascii=False
        ),
        "lineas_json": json.dumps(lineas, cls=DjangoJSONEncoder, ensure_ascii=False),
        "plantas_json": json.dumps(plantas, cls=DjangoJSONEncoder, ensure_ascii=False),
        "modo_demo": caso is None,
        "tipos_apuntamiento": ch.TipoApuntamiento.choices,
    }
    return render(request, "inspecciones/visor_plano_metrado.html", ctx)


@staff_member_required
@require_http_methods(["POST"])
def visor_plano_metrado_guardar(request, pk: int):
    caso = get_object_or_404(CasoRojo, pk=pk)
    if not usuario_puede_ver_caso(request.user, caso):
        return JsonResponse({"error": "Sin permiso"}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    id_pln01 = (body.get("id_pln01") or "").strip()
    codigo = (body.get("codigo_partida") or "").strip().upper()
    piso = (body.get("piso_pln") or "").strip().upper()
    if not id_pln01:
        return JsonResponse({"error": "id_pln01 es obligatorio"}, status=400)

    if body.get("eliminar"):
        qs = caso.lineas_metrado.filter(id_pln01__iexact=id_pln01)
        if codigo:
            qs = qs.filter(codigo_partida__iexact=codigo)
        qs.delete()
        return JsonResponse(
            {
                "ok": True,
                "lineas": _lineas_payload(caso),
                "plantas": _plantas_payload(caso),
            }
        )

    if not codigo:
        return JsonResponse({"error": "codigo_partida es obligatorio"}, status=400)

    # Asegurar prefijo de piso en id
    if piso and not id_pln01.upper().startswith(piso + "-"):
        # id ya puede traer piso (PB-C-A4); no forzar
        pass
    if not piso and "-" in id_pln01:
        piso = id_pln01.split("-", 1)[0].strip().upper()

    # Crear planta si no existe
    if piso:
        PlantaInspeccion.objects.get_or_create(
            caso=caso,
            codigo_piso=piso,
            defaults={
                "titulo": f"Planta {piso}",
                "orden": caso.plantas_inspeccion.count() + 1,
            },
        )

    partida = PartidaCatalogo.objects.filter(codigo__iexact=codigo, activo=True).first()
    ln = (
        caso.lineas_metrado.filter(id_pln01__iexact=id_pln01, codigo_partida__iexact=codigo).first()
        or caso.lineas_metrado.filter(id_pln01__iexact=id_pln01).order_by("orden", "id").first()
    )
    if ln is None:
        max_orden = caso.lineas_metrado.order_by("-orden").values_list("orden", flat=True).first() or 0
        ln = LineaMetrado(caso=caso, orden=max_orden + 1)

    ln.id_pln01 = id_pln01
    ln.piso_pln = piso or ln.piso_pln
    ln.codigo_partida = codigo
    ln.partida = partida
    ln.elemento = (body.get("elemento") or ln.elemento or ch.ElementoMetrado.PENDIENTE)[:32]
    ln.tipo_apuntamiento = (body.get("tipo_apuntamiento") or "na")[:16]
    ln.nota = (body.get("nota") or "")[:500]
    ln.ubicacion = (body.get("ubicacion") or ln.ubicacion or "")[:128]
    cant = body.get("cantidad")
    if cant in (None, ""):
        ln.cantidad = None
    else:
        try:
            from decimal import Decimal

            ln.cantidad = Decimal(str(cant))
        except Exception:
            ln.cantidad = None
    if partida and partida.unidad_default:
        ln.unidad = partida.unidad_default
    ln.save()
    return JsonResponse(
        {
            "ok": True,
            "lineas": _lineas_payload(caso),
            "plantas": _plantas_payload(caso),
        }
    )
