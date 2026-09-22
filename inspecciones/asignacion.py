"""Lógica de asignación en cascada: Admin → Coordinador → Ingeniero (+ revisor)."""
from __future__ import annotations

import re

from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet

from inspecciones.models import CasoRojo
from inspecciones.workflow import (
    GRUPO_COORDINADOR,
    GRUPO_INSPECTOR,
    GRUPO_REVISOR,
    es_administrador,
    es_solo_coordinador,
    filtrar_casos_por_rol,
)


_RE_EQUIPO = re.compile(r"^(?:coord|ing)\.equipo(\d+)", re.I)


def equipo_de_username(username: str) -> str | None:
    """Extrae N de coord.equipoN / ing.equipoN.x → 'N'."""
    m = _RE_EQUIPO.match(username or "")
    return m.group(1) if m else None


def opciones_usuario_select(qs) -> list[dict]:
    """Opciones de <select> con etiqueta legible (nombre · equipo · username)."""
    mapa = _mapa_nombres_equipo()
    out = []
    for u in qs:
        ui = etiqueta_usuario_ui(
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            mapa_equipos=mapa,
        )
        if ui["equipo"]:
            label = f"{ui['nombre']} · {ui['equipo']} ({u.username})"
        else:
            label = f"{ui['nombre']} ({u.username})"
        out.append({"pk": u.pk, "label": label, "username": u.username})
    return out


def _mapa_nombres_equipo() -> dict[str, str]:
    """numero(str) → nombre etiqueta (caché por proceso)."""
    from inspecciones.models import EquipoBrigada

    return {
        str(e.numero): (e.nombre or "").strip()
        for e in EquipoBrigada.objects.filter(activo=True).only("numero", "nombre")
    }


def etiqueta_equipo(numero: str | int | None, *, mapa: dict[str, str] | None = None) -> str:
    """Etiqueta legible: «Equipo 1 — Ataguia» o «Equipo 4» si aún no hay nombre."""
    if numero is None or str(numero).strip() == "":
        return "—"
    n = str(numero).strip()
    nombres = mapa if mapa is not None else _mapa_nombres_equipo()
    nombre = (nombres.get(n) or "").strip()
    if nombre and nombre.lower() != f"equipo {n}".lower():
        return f"Equipo {n} — {nombre}"
    return f"Equipo {n}"


def equipos_con_etiqueta() -> list[dict[str, str]]:
    """Lista [{numero, etiqueta, nombre}] ordenada para filtros UI."""
    nums: set[str] = set()
    qs = User.objects.filter(is_active=True).filter(
        Q(username__istartswith="coord.equipo") | Q(username__istartswith="ing.equipo")
    ).values_list("username", flat=True)
    for username in qs:
        eq = equipo_de_username(username)
        if eq:
            nums.add(eq)
    mapa = _mapa_nombres_equipo()
    out = []
    for eq in sorted(nums, key=lambda x: int(x) if x.isdigit() else 0):
        out.append(
            {
                "numero": eq,
                "nombre": mapa.get(eq, ""),
                "etiqueta": etiqueta_equipo(eq, mapa=mapa),
            }
        )
    return out


def usuarios_por_rol(viewer: User | None = None) -> dict[str, QuerySet]:
    """
    Usuarios activos por rol.
    Coordinador: solo ingenieros de su equipo (+ todos los revisores).
    Admin: todos.
    """
    base = (
        User.objects.filter(is_active=True)
        .exclude(username__endswith=".demo")
        .order_by("last_name", "first_name", "username")
    )
    inspectores = base.filter(groups__name=GRUPO_INSPECTOR, is_superuser=False).distinct()
    revisores = base.filter(groups__name=GRUPO_REVISOR, is_superuser=False).distinct()
    coordinadores = base.filter(groups__name=GRUPO_COORDINADOR, is_superuser=False).distinct()

    if viewer is not None and es_solo_coordinador(viewer):
        eq = equipo_de_username(viewer.username)
        if eq:
            inspectores = inspectores.filter(username__startswith=f"ing.equipo{eq}.")
        else:
            inspectores = inspectores.none()
        # El coordinador no administra otros coordinadores en el tablero
        coordinadores = coordinadores.filter(pk=viewer.pk)

    return {
        "inspectores": inspectores,
        "revisores": revisores,
        "coordinadores": coordinadores,
    }


def nombre_persona(first_name: str, last_name: str, username: str) -> tuple[str, bool]:
    """
    Nombre para UI. Devuelve (texto, es_nombre_real).
    Los placeholders de alta (Coordinador/Ingeniero/Revisor …) no cuentan como nombre real.
    """
    full = f"{(first_name or '').strip()} {(last_name or '').strip()}".strip()
    if not full:
        return username, False
    low = full.lower()
    if low.startswith(("coordinador", "ingeniero", "revisor", "equipo ")):
        return full, False
    return full, True


def etiqueta_usuario_ui(
    *,
    username: str,
    first_name: str = "",
    last_name: str = "",
    mapa_equipos: dict[str, str] | None = None,
) -> dict[str, str]:
    """Bloque listo para plantillas: nombre, username, equipo."""
    nombre, es_real = nombre_persona(first_name, last_name, username)
    eq = equipo_de_username(username)
    return {
        "nombre": nombre,
        "es_nombre_real": es_real,
        "username": username,
        "equipo_num": eq or "",
        "equipo": etiqueta_equipo(eq, mapa=mapa_equipos) if eq else "",
        "etiqueta_corta": (
            f"{nombre} · {etiqueta_equipo(eq, mapa=mapa_equipos)}"
            if eq
            else nombre
        ),
    }


def resumen_usuarios(viewer: User | None = None) -> list[dict]:
    """Filas del tablero de carga; alcance según quien mira."""
    roles_map: dict[int, list[str]] = {}
    por_rol = usuarios_por_rol(viewer)
    for rol, nombre in (
        ("inspectores", "Inspector"),
        ("revisores", "Revisor"),
        ("coordinadores", "Coordinador"),
    ):
        for user in por_rol[rol]:
            roles_map.setdefault(user.pk, []).append(nombre)

    user_ids = list(roles_map.keys())
    if not user_ids:
        return []

    # Conteos: admin = globales; coordinador = solo dentro de su bolsa
    if viewer is not None and es_solo_coordinador(viewer):
        stats_qs = User.objects.filter(pk__in=user_ids).annotate(
            n_inspector=Count(
                "casos_inspeccion",
                filter=Q(casos_inspeccion__coordinador_asignado=viewer),
                distinct=True,
            ),
            n_revisor=Count(
                "casos_revision",
                filter=Q(casos_revision__coordinador_asignado=viewer),
                distinct=True,
            ),
            n_coord=Count(
                "casos_coordinacion",
                filter=Q(casos_coordinacion__coordinador_asignado=viewer),
                distinct=True,
            ),
        )
    else:
        stats_qs = User.objects.filter(pk__in=user_ids).annotate(
            n_inspector=Count("casos_inspeccion", distinct=True),
            n_revisor=Count("casos_revision", distinct=True),
            n_coord=Count("casos_coordinacion", distinct=True),
        )

    stats = {
        row["pk"]: row
        for row in stats_qs.values(
            "pk",
            "username",
            "first_name",
            "last_name",
            "n_inspector",
            "n_revisor",
            "n_coord",
        )
    }

    mapa_eq = _mapa_nombres_equipo()
    filas = []
    for uid in user_ids:
        row = stats[uid]
        ui = etiqueta_usuario_ui(
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            mapa_equipos=mapa_eq,
        )
        filas.append(
            {
                "id": uid,
                "username": row["username"],
                "nombre": ui["nombre"],
                "es_nombre_real": ui["es_nombre_real"],
                "equipo": ui["equipo"],
                "equipo_num": ui["equipo_num"],
                "roles": roles_map[uid],
                "n_inspector": row["n_inspector"],
                "n_revisor": row["n_revisor"],
                "n_coord": row["n_coord"],
                "total": row["n_inspector"] + row["n_revisor"] + row["n_coord"],
            }
        )
    # Orden: por número de equipo, luego nombre
    filas.sort(
        key=lambda r: (
            int(r["equipo_num"]) if str(r["equipo_num"]).isdigit() else 999,
            r["nombre"].lower(),
            r["username"],
        )
    )
    return filas


def resumen_usuarios_por_equipo(viewer: User | None = None) -> list[dict]:
    """Agrupa resumen_usuarios por brigada para UI plegable."""
    filas = resumen_usuarios(viewer)
    grupos: dict[str, dict] = {}
    orden: list[str] = []
    for u in filas:
        num = str(u.get("equipo_num") or "").strip()
        key = num if num else "_sin"
        if key not in grupos:
            etiqueta = u.get("equipo") or "Sin equipo / transversal"
            if key == "_sin":
                etiqueta = "Sin equipo / revisores transversales"
            grupos[key] = {
                "key": key,
                "numero": num,
                "etiqueta": etiqueta,
                "usuarios": [],
                "n_personas": 0,
                "n_inspector": 0,
                "n_revisor": 0,
                "n_coord": 0,
            }
            orden.append(key)
        g = grupos[key]
        g["usuarios"].append(u)
        g["n_personas"] += 1
        g["n_inspector"] += int(u.get("n_inspector") or 0)
        g["n_revisor"] += int(u.get("n_revisor") or 0)
        g["n_coord"] += int(u.get("n_coord") or 0)
    # Orden numérico de equipos; sin equipo al final
    orden.sort(key=lambda k: int(k) if k.isdigit() else 999)
    return [grupos[k] for k in orden]


def kpis_asignacion(user=None) -> dict[str, int]:
    from inspecciones import choices as ch

    qs = filtrar_casos_por_rol(user) if user is not None else CasoRojo.objects.all()
    total = qs.count()
    sin_coord = qs.filter(coordinador_asignado__isnull=True).count()
    sin_inspector = qs.filter(inspector_asignado__isnull=True).count()
    return {
        "total": total,
        "sin_coordinador": sin_coord,
        "sin_inspector": sin_inspector,
        "con_inspector": qs.filter(inspector_asignado__isnull=False).count(),
        "en_bandeja_revision": qs.filter(
            estado_2da=ch.Estado2daRonda.PENDIENTE_REVISION
        ).count(),
        # Legado (plantillas/guías antiguas): no usar como KPI operativo
        "sin_revisor": qs.filter(revisor_asignado__isnull=True).count(),
        "con_ambos": qs.filter(
            inspector_asignado__isnull=False, revisor_asignado__isnull=False
        ).count(),
    }


def filtrar_casos(request) -> QuerySet:
    from django.db.models import CharField
    from django.db.models.functions import Cast
    from inspecciones import choices as ch

    qs = filtrar_casos_por_rol(
        request.user,
        CasoRojo.objects.select_related(
            "coordinador_asignado", "inspector_asignado", "revisor_asignado"
        ),
    )
    estado = request.GET.get("estado", "").strip()
    banda = request.GET.get("banda", "").strip()
    sin_inspector = request.GET.get("sin_inspector")
    sin_revisor = request.GET.get("sin_revisor")
    en_revision = request.GET.get("en_revision")
    sin_coordinador = request.GET.get("sin_coordinador")
    usuario_id = request.GET.get("usuario")
    rol_usuario = request.GET.get("rol", "inspector")
    q = request.GET.get("q", "").strip()
    certificado = request.GET.get("certificado", "").strip()
    ubicacion = request.GET.get("ubicacion", "").strip()

    if estado:
        qs = qs.filter(estado_2da=estado)
    if banda:
        qs = qs.filter(banda=banda)
    if sin_inspector == "1":
        qs = qs.filter(inspector_asignado__isnull=True)
    if en_revision == "1":
        qs = qs.filter(estado_2da=ch.Estado2daRonda.PENDIENTE_REVISION)
    if sin_revisor == "1":
        # Compat filtros antiguos / enlaces legacy
        qs = qs.filter(revisor_asignado__isnull=True)
    if sin_coordinador == "1" and es_administrador(request.user):
        qs = qs.filter(coordinador_asignado__isnull=True)
    if usuario_id:
        try:
            uid = int(usuario_id)
            if rol_usuario == "revisor":
                qs = qs.filter(revisor_asignado_id=uid)
            elif rol_usuario == "coordinador":
                qs = qs.filter(coordinador_asignado_id=uid)
            else:
                qs = qs.filter(inspector_asignado_id=uid)
        except ValueError:
            pass
    if certificado:
        qs = qs.filter(certificado__icontains=certificado)
    if ubicacion:
        qs = qs.filter(
            Q(muni_parr__icontains=ubicacion)
            | Q(direccion_hab__icontains=ubicacion)
            | Q(corr_muni_parr__icontains=ubicacion)
            | Q(corr_direccion__icontains=ubicacion)
        )
    if q:
        qs = qs.annotate(_hab_txt=Cast("hab_id", output_field=CharField()))
        # Varios términos (AND): cada uno debe coincidir en identidad o ubicación.
        tokens = [t for t in q.replace(",", " ").split() if t]
        for tok in tokens:
            clause = (
                Q(nombre_hab__icontains=tok)
                | Q(nombre_conf__icontains=tok)
                | Q(direccion_hab__icontains=tok)
                | Q(muni_parr__icontains=tok)
                | Q(certificado__icontains=tok)
                | Q(etiqueta_f1__icontains=tok)
                | Q(gps_hab__icontains=tok)
                | Q(corr_nombre__icontains=tok)
                | Q(corr_direccion__icontains=tok)
                | Q(corr_muni_parr__icontains=tok)
                | Q(_hab_txt__icontains=tok)
            )
            if tok.isdigit():
                n = int(tok)
                clause |= Q(hab_id=n) | Q(pk=n)
            qs = qs.filter(clause)
    return qs.order_by("-score", "hab_id")


def aplicar_asignacion(
    casos: QuerySet,
    *,
    user,
    coordinador_id: int | None = None,
    inspector_id: int | None = None,
    revisor_id: int | None = None,
    limpiar_coordinador: bool = False,
    limpiar_inspector: bool = False,
    limpiar_revisor: bool = False,
) -> int:
    """Actualiza asignaciones en lote según rol de quien asigna."""
    update_fields = ["updated_at"]
    values: dict = {}

    es_admin = es_administrador(user)

    if es_admin:
        if limpiar_coordinador:
            values["coordinador_asignado_id"] = None
            update_fields.append("coordinador_asignado_id")
        elif coordinador_id:
            values["coordinador_asignado_id"] = coordinador_id
            update_fields.append("coordinador_asignado_id")

    if limpiar_inspector:
        values["inspector_asignado_id"] = None
        update_fields.append("inspector_asignado_id")
    elif inspector_id:
        # Coordinador solo puede asignar ingenieros de su equipo
        if not es_admin:
            dest = User.objects.filter(pk=inspector_id).first()
            eq_self = equipo_de_username(user.username)
            eq_dest = equipo_de_username(dest.username) if dest else None
            if not dest or eq_self != eq_dest:
                return 0
        values["inspector_asignado_id"] = inspector_id
        update_fields.append("inspector_asignado_id")

    if limpiar_revisor:
        values["revisor_asignado_id"] = None
        update_fields.append("revisor_asignado_id")
    elif revisor_id:
        values["revisor_asignado_id"] = revisor_id
        update_fields.append("revisor_asignado_id")

    if len(update_fields) == 1:
        return 0

    if not es_admin:
        casos = casos.filter(coordinador_asignado=user)

    return casos.update(**values)
