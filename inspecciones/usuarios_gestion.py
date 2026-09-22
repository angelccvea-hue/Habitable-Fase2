"""Gestión operativa de usuarios (solo administrador): altas, claves, carga."""
from __future__ import annotations

import re
import secrets
import string
from typing import Any

from django.db.models import Count
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType

from inspecciones.asignacion import equipo_de_username, etiqueta_usuario_ui
from inspecciones.models import (
    CasoRojo,
    CredencialEmitida,
    CroquisAdjunto,
    EvidenciaFoto,
    HistorialDetallado,
    HistorialEstado,
    InformePdfAdjunto,
    LineaMetrado,
    PartidaCatalogo,
    Procedimiento,
)
from inspecciones.workflow import (
    GRUPO_CONSULTA,
    GRUPO_COORDINADOR,
    GRUPO_INSPECTOR,
    GRUPO_REVISOR,
    asegurar_grupos,
)

ROLES_ALTA = (
    ("coordinador", "Coordinador de equipo"),
    ("inspector", "Ingeniero / Inspector"),
    ("revisor", "Revisor técnico"),
    ("consulta", "Consulta (solo lectura)"),
)

_LETTERS = list("abcdefghijklmnopqrstuvwxyz")


def generar_clave(prefix: str, *, largo: int = 8) -> str:
    """Mismo estilo operativo: Prefijo-XXXXXXXX (letras/dígitos)."""
    alphabet = string.ascii_letters + string.digits
    tail = "".join(secrets.choice(alphabet) for _ in range(largo))
    clean = re.sub(r"[^A-Za-z0-9]", "", prefix) or "User"
    return f"{clean}-{tail}"


def _perms(model, acciones: tuple[str, ...]) -> list[Permission]:
    ct = ContentType.objects.get_for_model(model)
    codes = [f"{a}_{model._meta.model_name}" for a in acciones]
    return list(Permission.objects.filter(content_type=ct, codename__in=codes))


def asegurar_permisos_grupos() -> dict:
    """Alinea permisos Django de los grupos CPEH (idempotente)."""
    grupos = asegurar_grupos()
    caso_rw = _perms(CasoRojo, ("view", "add", "change"))
    caso_all = _perms(CasoRojo, ("view", "add", "change", "delete"))
    caso_v = _perms(CasoRojo, ("view",))
    proc_v = _perms(Procedimiento, ("view",))
    hist_v = _perms(HistorialEstado, ("view",))
    hist_det_v = _perms(HistorialDetallado, ("view",))
    foto_rw = _perms(EvidenciaFoto, ("view", "add", "change"))
    foto_all = _perms(EvidenciaFoto, ("view", "add", "change", "delete"))
    foto_v = _perms(EvidenciaFoto, ("view",))
    pdf_rw = _perms(InformePdfAdjunto, ("view", "add", "change"))
    pdf_all = _perms(InformePdfAdjunto, ("view", "add", "change", "delete"))
    pdf_v = _perms(InformePdfAdjunto, ("view",))
    cro_rw = _perms(CroquisAdjunto, ("view", "add", "change"))
    cro_all = _perms(CroquisAdjunto, ("view", "add", "change", "delete"))
    cro_v = _perms(CroquisAdjunto, ("view",))
    # Metrados: sin estos permisos el inline no aparece y el autocomplete de
    # partidas falla (ingenieros no podían cargar cuantificación en ficha).
    metrado_rw = _perms(LineaMetrado, ("view", "add", "change"))
    metrado_all = _perms(LineaMetrado, ("view", "add", "change", "delete"))
    partida_v = _perms(PartidaCatalogo, ("view",))

    base_campo = (
        caso_rw
        + proc_v
        + hist_v
        + hist_det_v
        + foto_rw
        + pdf_rw
        + cro_rw
        + metrado_rw
        + partida_v
    )
    # Coordinadores: ver usuarios para menú Jazzmin «Asignación» / «Nombres del equipo»
    # y para elegir ingenieros/revisores en el tablero (auth.view_user).
    user_v = list(
        Permission.objects.filter(
            content_type__app_label="auth",
            codename__in=("view_user", "view_group"),
        )
    )
    grupos[GRUPO_INSPECTOR].permissions.set(base_campo)
    grupos[GRUPO_REVISOR].permissions.set(base_campo)
    grupos[GRUPO_COORDINADOR].permissions.set(
        caso_all
        + _perms(Procedimiento, ("view", "add", "change"))
        + hist_v
        + hist_det_v
        + foto_all
        + pdf_all
        + cro_all
        + metrado_all
        + partida_v
        + user_v
    )
    grupos[GRUPO_CONSULTA].permissions.set(
        caso_v
        + proc_v
        + hist_v
        + hist_det_v
        + foto_v
        + pdf_v
        + cro_v
        + _perms(LineaMetrado, ("view",))
        + partida_v
    )
    return grupos


def guardar_clave_emitida(
    user: User,
    password: str,
    *,
    por: User | None = None,
    nota: str = "",
) -> CredencialEmitida:
    cred, _ = CredencialEmitida.objects.update_or_create(
        user=user,
        defaults={
            "password_plain": password,
            "emitida_por": por,
            "nota": (nota or "")[:255],
        },
    )
    return cred


def emitir_clave(user: User, *, por: User | None = None, prefix: str | None = None) -> str:
    """Genera clave, la aplica al usuario y la guarda para el panel admin."""
    pref = prefix or _prefix_desde_username(user.username)
    password = generar_clave(pref)
    user.set_password(password)
    user.save(update_fields=["password"])
    guardar_clave_emitida(user, password, por=por, nota="Regenerada desde gestión")
    return password


def _prefix_desde_username(username: str) -> str:
    u = (username or "").lower()
    m = re.match(r"^coord\.equipo(\d+)$", u)
    if m:
        return f"Coord{m.group(1)}"
    m = re.match(r"^ing\.equipo(\d+)\.([a-z])$", u)
    if m:
        return f"Ing{m.group(1)}{m.group(2).upper()}"
    m = re.match(r"^revisor\.(\d+)$", u)
    if m:
        return f"Rev{m.group(1)}"
    m = re.match(r"^consulta\.(\d+)$", u)
    if m:
        return f"Consulta{m.group(1)}"
    if u.startswith("admin"):
        return "AdmOp"
    return "User"


def _siguiente_letra_inspector(equipo: int) -> str:
    usados = set(
        User.objects.filter(username__regex=rf"^ing\.equipo{equipo}\.[a-z]$").values_list(
            "username", flat=True
        )
    )
    for letter in _LETTERS:
        if f"ing.equipo{equipo}.{letter}" not in usados:
            return letter
    raise ValueError(f"No quedan letras libres para ingenieros del equipo {equipo}.")


def _siguiente_numero(patron: str) -> int:
    """patron con grupo captura del número, p.ej. r'^revisor\\.(\\d+)$'."""
    nums = []
    for username in User.objects.filter(username__regex=patron).values_list(
        "username", flat=True
    ):
        m = re.match(patron, username)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def proponer_username(rol: str, equipo: int | None = None) -> str:
    rol = (rol or "").strip().lower()
    if rol == "coordinador":
        if not equipo:
            raise ValueError("Indique el número de equipo para el coordinador.")
        return f"coord.equipo{equipo}"
    if rol == "inspector":
        if not equipo:
            raise ValueError("Indique el número de equipo para el ingeniero.")
        letter = _siguiente_letra_inspector(equipo)
        return f"ing.equipo{equipo}.{letter}"
    if rol == "revisor":
        n = _siguiente_numero(r"^revisor\.(\d+)$")
        return f"revisor.{n}"
    if rol == "consulta":
        n = _siguiente_numero(r"^consulta\.(\d+)$")
        return f"consulta.{n}"
    raise ValueError(f"Rol no reconocido: {rol}")


def crear_usuario_operativo(
    *,
    rol: str,
    first_name: str,
    last_name: str,
    equipo: int | None = None,
    username: str | None = None,
    email: str | None = None,
    por: User | None = None,
    activo: bool = True,
) -> dict[str, Any]:
    """
    Crea usuario staff con grupo CPEH, clave estilo Prefijo-XXXX y credencial emitida.
    """
    grupos = asegurar_permisos_grupos()
    rol = (rol or "").strip().lower()
    first_name = (first_name or "").strip()[:150]
    last_name = (last_name or "").strip()[:150]
    if not first_name and not last_name:
        raise ValueError("Indique al menos nombre o apellido.")

    if username:
        username = username.strip().lower()
    else:
        username = proponer_username(rol, equipo)

    if User.objects.filter(username=username).exists():
        raise ValueError(f"Ya existe el usuario «{username}».")

    mapa_grupo = {
        "coordinador": GRUPO_COORDINADOR,
        "inspector": GRUPO_INSPECTOR,
        "revisor": GRUPO_REVISOR,
        "consulta": GRUPO_CONSULTA,
    }
    if rol not in mapa_grupo:
        raise ValueError(f"Rol no válido: {rol}")

    prefix = _prefix_desde_username(username)
    password = generar_clave(prefix)
    email = (email or f"{username}@cpeh.local").strip()[:254]

    user = User.objects.create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_staff=True,
        is_active=activo,
        is_superuser=False,
    )
    user.set_password(password)
    user.save()
    user.groups.set([grupos[mapa_grupo[rol]]])
    guardar_clave_emitida(user, password, por=por, nota=f"Alta {rol}")

    return {
        "user": user,
        "username": username,
        "password": password,
        "rol": rol,
        "equipo": equipo_de_username(username),
    }


def roles_etiqueta(user: User) -> list[str]:
    if user.is_superuser:
        return ["Administrador"]
    labels = {
        GRUPO_COORDINADOR: "Coordinador",
        GRUPO_INSPECTOR: "Inspector",
        GRUPO_REVISOR: "Revisor",
        GRUPO_CONSULTA: "Consulta",
    }
    out = []
    for name in user.groups.values_list("name", flat=True):
        if name in labels:
            out.append(labels[name])
    return out or ["Staff"]


def listar_usuarios_gestion() -> list[dict[str, Any]]:
    """Filas del tablero admin: datos + carga de casos + clave emitida."""
    from inspecciones import choices as ch

    qs = (
        User.objects.filter(is_staff=True)
        .prefetch_related("groups")
        .annotate(
            n_inspector=Count("casos_inspeccion", distinct=True),
            n_revisor=Count("casos_revision", distinct=True),
            n_coord=Count("casos_coordinacion", distinct=True),
            n_historial=Count("historialestado", distinct=True),
        )
        .order_by("-is_active", "username")
    )
    creds = {
        c.user_id: c
        for c in CredencialEmitida.objects.select_related("emitida_por").all()
    }
    proc_estados = [
        ch.Estado2daRonda.PENDIENTE_REVISION,
        ch.Estado2daRonda.REVISADO,
        ch.Estado2daRonda.APROBADO,
        ch.Estado2daRonda.PUBLICADO,
    ]

    filas = []
    for u in qs:
        ui = etiqueta_usuario_ui(
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
        )
        cred = creds.get(u.pk)
        roles = roles_etiqueta(u)
        if "Coordinador" in roles:
            n_proc = CasoRojo.objects.filter(
                coordinador_asignado=u, estado_2da__in=proc_estados
            ).count()
        elif "Inspector" in roles:
            n_proc = CasoRojo.objects.filter(
                inspector_asignado=u, estado_2da__in=proc_estados
            ).count()
        elif "Revisor" in roles:
            n_proc = CasoRojo.objects.filter(
                revisor_asignado=u, estado_2da__in=proc_estados
            ).count()
        else:
            n_proc = 0

        filas.append(
            {
                "id": u.pk,
                "username": u.username,
                "nombre": ui["nombre"],
                "es_nombre_real": ui["es_nombre_real"],
                "email": u.email,
                "activo": u.is_active,
                "superuser": u.is_superuser,
                "roles": roles,
                "equipo": ui["equipo"] or "—",
                "n_inspector": u.n_inspector,
                "n_revisor": u.n_revisor,
                "n_coord": u.n_coord,
                "n_asignados": u.n_inspector + u.n_revisor + u.n_coord,
                "n_procesados": n_proc,
                "n_historial": u.n_historial,
                "clave": cred.password_plain if cred else "",
                "clave_en": cred.emitida_en if cred else None,
                "last_login": u.last_login,
                "date_joined": u.date_joined,
            }
        )
    return filas


def set_activo(user: User, activo: bool) -> None:
    if user.is_superuser and not activo:
        raise ValueError("No se puede desactivar un administrador desde este panel.")
    user.is_active = activo
    user.save(update_fields=["is_active"])
