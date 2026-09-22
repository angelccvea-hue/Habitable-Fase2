"""KPIs compactos para la portada del admin (alcance por rol)."""
from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, QuerySet
from django.utils import timezone

from inspecciones import choices as ch
from inspecciones.asignacion import (
    equipo_de_username,
    equipos_con_etiqueta,
    etiqueta_equipo,
    usuarios_por_rol,
)
from inspecciones.models import CasoRojo
from inspecciones.workflow import (
    es_administrador,
    es_solo_consulta,
    es_solo_coordinador,
    es_solo_inspector,
    es_solo_revisor,
    filtrar_casos_por_rol,
    ve_todos_los_casos,
)

CR_PAGE_SIZE = 20
RA_PAGE_SIZE = 20


def _page_links(*, get, page_param: str, page_obj, keep_prefixes: tuple[str, ...], anchor: str) -> dict:
    """Metadatos de paginación + URLs prev/next/números (máx. 7 botones)."""
    total_pages = page_obj.paginator.num_pages
    current = page_obj.number
    base = []
    for pref in keep_prefixes:
        base.extend(_params_with_prefix(get, pref))
    base = [(k, v) for k, v in base if k != page_param]

    def _url(n: int) -> str:
        params = list(base) + [(page_param, str(n))]
        return f"/admin/?{urlencode(params)}#{anchor}"

    if total_pages <= 7:
        window = list(range(1, total_pages + 1))
    else:
        start = max(1, current - 2)
        end = min(total_pages, start + 4)
        start = max(1, end - 4)
        window = list(range(start, end + 1))

    return {
        "page": current,
        "num_pages": total_pages,
        "has_prev": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "prev_url": _url(page_obj.previous_page_number()) if page_obj.has_previous() else "",
        "next_url": _url(page_obj.next_page_number()) if page_obj.has_next() else "",
        "first_url": _url(1) if current > 1 else "",
        "last_url": _url(total_pages) if current < total_pages else "",
        "pages": [{"n": n, "url": _url(n), "active": n == current} for n in window],
        "showing_from": page_obj.start_index() if page_obj.paginator.count else 0,
        "showing_to": page_obj.end_index() if page_obj.paginator.count else 0,
        "per_page": page_obj.paginator.per_page,
    }


def _casos_url(**params) -> str:
    base = "/admin/inspecciones/casorojo/"
    if not params:
        return base
    return f"{base}?{urlencode(params)}"


def _kpi(label: str, value: int, icon: str, css_class: str, url: str | None = None) -> dict:
    return {
        "label": label,
        "value": value,
        "icon": icon,
        "class": css_class,
        "url": url or _casos_url(),
    }


def get_dashboard_context(request=None) -> dict:
    user = getattr(request, "user", None) if request else None
    if user and user.is_authenticated:
        qs = filtrar_casos_por_rol(user)
        alcance_global = ve_todos_los_casos(user)
        if es_administrador(user):
            label_total = "Casos totales"
        elif es_solo_consulta(user):
            label_total = "Casos (solo lectura)"
        elif es_solo_revisor(user):
            label_total = "Casos (consulta)"
        elif es_solo_coordinador(user):
            label_total = "Mi bolsa"
        else:
            label_total = "Mis casos"
    else:
        qs = CasoRojo.objects.none()
        alcance_global = False
        label_total = "Casos"

    total = qs.count()
    kpis: list[dict] = []
    cola_revision = qs.none()
    titulo_recientes = "Casos recientes"
    vacio_cola_msg = ""

    if user and user.is_authenticated and es_solo_revisor(user):
        # Bandeja compartida: todos los Pendiente revisión (+ Revisado legado)
        cola_revision = qs.filter(
            estado_2da__in=ch.ESTADOS_COLA_REVISION
        ).order_by("-score", "-updated_at")
        url_para_revisar = _casos_url(
            estado_2da__exact=ch.Estado2daRonda.PENDIENTE_REVISION
        )
        kpis.extend(
            [
                _kpi(
                    "Bandeja por revisión",
                    cola_revision.count(),
                    "fas fa-inbox",
                    "kpi-yellow",
                    url_para_revisar,
                ),
                _kpi(label_total, total, "fas fa-building", "kpi-blue"),
            ]
        )
        titulo_recientes = "Bandeja por revisión (Pendiente revisión)"
        n_cola = cola_revision.count()
        vacio_cola_msg = (
            "No hay casos en «Pendiente revisión». Aparecerán aquí cuando un ingeniero "
            "complete el informe y lo envíe a revisión (bandeja compartida: no hace falta asignar revisor)."
            if n_cola == 0
            else ""
        )
        base_recientes = cola_revision
        if not base_recientes.exists():
            base_recientes = qs.order_by("-updated_at")
            titulo_recientes = "Casos recientes (consulta — bandeja vacía)"
        else:
            base_recientes = cola_revision
    else:
        kpis.append(_kpi(label_total, total, "fas fa-building", "kpi-blue"))
        if user and user.is_authenticated and es_administrador(user):
            kpis.extend(
                [
                    _kpi(
                        "Sin coordinador",
                        qs.filter(coordinador_asignado__isnull=True).count(),
                        "fas fa-user-tie",
                        "kpi-yellow",
                        "/asignacion/?sin_coordinador=1",
                    ),
                    _kpi(
                        "Sin inspector",
                        qs.filter(inspector_asignado__isnull=True).count(),
                        "fas fa-user-slash",
                        "kpi-yellow",
                        "/asignacion/?sin_inspector=1",
                    ),
                    _kpi(
                        "Bandeja por revisión",
                        qs.filter(
                            estado_2da=ch.Estado2daRonda.PENDIENTE_REVISION
                        ).count(),
                        "fas fa-inbox",
                        "kpi-yellow",
                        _casos_url(
                            estado_2da__exact=ch.Estado2daRonda.PENDIENTE_REVISION
                        ),
                    ),
                ]
            )
        elif user and user.is_authenticated and es_solo_coordinador(user):
            kpis.extend(
                [
                    _kpi(
                        "Sin inspector",
                        qs.filter(inspector_asignado__isnull=True).count(),
                        "fas fa-user-slash",
                        "kpi-yellow",
                        "/asignacion/?sin_inspector=1",
                    ),
                    _kpi(
                        "Bandeja por revisión",
                        qs.filter(
                            estado_2da=ch.Estado2daRonda.PENDIENTE_REVISION
                        ).count(),
                        "fas fa-inbox",
                        "kpi-yellow",
                        _casos_url(
                            estado_2da__exact=ch.Estado2daRonda.PENDIENTE_REVISION
                        ),
                    ),
                ]
            )
        base_recientes = qs.order_by("-updated_at")

    # KPIs de decisión / estado (con enlace filtrado)
    kpis.extend(
        [
            _kpi(
                "D1 Complementos",
                qs.filter(decision_D=ch.DecisionD.D1).count(),
                "fas fa-tasks",
                "kpi-blue",
                _casos_url(decision_D__exact=ch.DecisionD.D1),
            ),
            _kpi(
                "D2 Reparar",
                qs.filter(decision_D=ch.DecisionD.D2).count(),
                "fas fa-tools",
                "kpi-yellow",
                _casos_url(decision_D__exact=ch.DecisionD.D2),
            ),
            _kpi(
                "D3 Demoler",
                qs.filter(decision_D=ch.DecisionD.D3).count(),
                "fas fa-exclamation-triangle",
                "kpi-red",
                _casos_url(decision_D__exact=ch.DecisionD.D3),
            ),
            _kpi(
                "D4 Escombros",
                qs.filter(decision_D=ch.DecisionD.D4).count(),
                "fas fa-dumpster",
                "kpi-red",
                _casos_url(decision_D__exact=ch.DecisionD.D4),
            ),
            _kpi(
                "Sin dictamen",
                qs.filter(decision_D=ch.DecisionD.PENDIENTE).count(),
                "fas fa-question-circle",
                "kpi-neutral",
                _casos_url(decision_D__exact=ch.DecisionD.PENDIENTE),
            ),
            _kpi(
                "Pend. verificación",
                qs.filter(estado_2da=ch.Estado2daRonda.PENDIENTE).count(),
                "fas fa-clock",
                "kpi-neutral",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.PENDIENTE),
            ),
            _kpi(
                "En visita",
                qs.filter(estado_2da=ch.Estado2daRonda.EN_VISITA).count(),
                "fas fa-hard-hat",
                "kpi-yellow",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.EN_VISITA),
            ),
            _kpi(
                "Borrador",
                qs.filter(estado_2da=ch.Estado2daRonda.BORRADOR).count(),
                "fas fa-pencil-alt",
                "kpi-blue",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.BORRADOR),
            ),
            _kpi(
                "Pend. revisión",
                qs.filter(estado_2da__in=ch.ESTADOS_COLA_REVISION).count(),
                "fas fa-clipboard-list",
                "kpi-yellow",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.PENDIENTE_REVISION),
            ),
            _kpi(
                "Revisados",
                qs.filter(estado_2da=ch.Estado2daRonda.REVISADO).count(),
                "fas fa-check",
                "kpi-green",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.REVISADO),
            ),
            _kpi(
                "Aprobados",
                qs.filter(estado_2da=ch.Estado2daRonda.APROBADO).count(),
                "fas fa-check-double",
                "kpi-green",
                _casos_url(estado_2da__exact=ch.Estado2daRonda.APROBADO),
            ),
            _kpi(
                "Prior. inmediata",
                qs.filter(prioridad=ch.PrioridadOperativa.INMEDIATA).count(),
                "fas fa-bolt",
                "kpi-red",
                _casos_url(prioridad__exact=ch.PrioridadOperativa.INMEDIATA),
            ),
            _kpi(
                "Prior. alta",
                qs.filter(prioridad=ch.PrioridadOperativa.ALTA).count(),
                "fas fa-fire",
                "kpi-red",
                _casos_url(prioridad__exact=ch.PrioridadOperativa.ALTA),
            ),
            _kpi("Score ≥ 70", qs.filter(score__gte=70).count(), "fas fa-chart-line", "kpi-red"),
            _kpi(
                "Con visita 2",
                qs.filter(fecha_v2__isnull=False).count(),
                "fas fa-calendar-check",
                "kpi-blue",
            ),
        ]
    )

    # Evitar duplicar «Pend. revisión» en revisor (ya está «Para revisar»)
    if user and user.is_authenticated and es_solo_revisor(user):
        kpis = [k for k in kpis if k["label"] != "Pend. revisión"]

    cr_ctx = get_casos_recientes_context(request, base_recientes, titulo_recientes)
    ctx = {
        "dashboard_kpis": kpis,
        "dashboard_total": total,
        "dashboard_alcance_global": alcance_global,
        "dashboard_vacio_cola_msg": vacio_cola_msg,
        "dashboard_es_revisor": bool(user and user.is_authenticated and es_solo_revisor(user)),
        "dashboard_url_cola": _casos_url(
            estado_2da__exact=ch.Estado2daRonda.PENDIENTE_REVISION
        ),
        "guia_usuario_aprobada": getattr(settings, "GUIA_USUARIO_PDF_APROBADA", False),
    }
    ctx.update(cr_ctx)
    ctx.update(get_recent_actions_context(request))
    # URLs limpiar preservando la otra sección
    get = getattr(request, "GET", None)
    ctx["cr_limpiar_url"] = _admin_query_url(get, keep_prefixes=("ra_",), anchor="casos-recientes")
    ctx["ra_limpiar_url"] = _admin_query_url(get, keep_prefixes=("cr_",), anchor="acciones-recientes")
    ctx["cr_hidden_ra"] = _params_with_prefix(get, "ra_")
    ctx["ra_hidden_cr"] = _params_with_prefix(get, "cr_")
    return ctx


def _parse_ymd(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _q_tokens(raw: str) -> list[str]:
    """Palabras clave (máx. 6) para búsqueda AND."""
    parts = [p.strip() for p in (raw or "").replace(",", " ").split() if p.strip()]
    return parts[:6]


def _filtrar_casos_por_q(qs: QuerySet, q_raw: str) -> QuerySet:
    """Búsqueda genérica: ID, edificio, dirección, municipio, decisión, estado, usuarios."""
    tokens = _q_tokens(q_raw)
    if not tokens:
        return qs
    for tok in tokens:
        if tok.isdigit():
            qs = qs.filter(
                Q(hab_id=int(tok))
                | Q(certificado__icontains=tok)
                | Q(nombre_hab__icontains=tok)
                | Q(nombre_conf__icontains=tok)
            )
        else:
            qs = qs.filter(
                Q(nombre_hab__icontains=tok)
                | Q(nombre_conf__icontains=tok)
                | Q(direccion_hab__icontains=tok)
                | Q(muni_parr__icontains=tok)
                | Q(certificado__icontains=tok)
                | Q(decision_D__icontains=tok)
                | Q(estado_2da__icontains=tok)
                | Q(coordinador_asignado__username__icontains=tok)
                | Q(inspector_asignado__username__icontains=tok)
                | Q(coordinador_asignado__first_name__icontains=tok)
                | Q(coordinador_asignado__last_name__icontains=tok)
            )
    return qs


def _filtrar_log_por_q(qs: QuerySet, q_raw: str) -> QuerySet:
    """Búsqueda genérica en LogEntry: ID caso, repr, mensaje, usuario."""
    tokens = _q_tokens(q_raw)
    if not tokens:
        return qs
    for tok in tokens:
        if tok.isdigit():
            qs = qs.filter(
                Q(object_id=tok)
                | Q(object_repr__icontains=tok)
                | Q(change_message__icontains=tok)
                | Q(user__username__icontains=tok)
            )
        else:
            qs = qs.filter(
                Q(object_repr__icontains=tok)
                | Q(change_message__icontains=tok)
                | Q(user__username__icontains=tok)
                | Q(user__first_name__icontains=tok)
                | Q(user__last_name__icontains=tok)
            )
    return qs


def _params_with_prefix(get, prefix: str) -> list[tuple[str, str]]:
    if not get:
        return []
    out: list[tuple[str, str]] = []
    for key in get.keys():
        if key.startswith(prefix):
            for val in get.getlist(key):
                out.append((key, val))
    return out


def _admin_query_url(get, keep_prefixes: tuple[str, ...], anchor: str) -> str:
    data: list[tuple[str, str]] = []
    if get:
        for prefix in keep_prefixes:
            data.extend(_params_with_prefix(get, prefix))
    q = urlencode(data)
    return f"/admin/?{q}#{anchor}" if q else f"/admin/#{anchor}"


def _filtrar_qs_por_equipo(qs: QuerySet, equipo: str) -> QuerySet:
    pref_coord = f"coord.equipo{equipo}"
    pref_ing = f"ing.equipo{equipo}."
    return qs.filter(
        Q(coordinador_asignado__username__iexact=pref_coord)
        | Q(coordinador_asignado__username__istartswith=f"{pref_coord}.")
        | Q(inspector_asignado__username__istartswith=pref_ing)
    )


# Campos ordenables de la tabla Casos recientes (clave GET → expresión ORM)
CR_SORT_FIELDS: dict[str, str] = {
    "id": "hab_id",
    "edificio": "edificio_ord",
    "score": "score",
    "decision": "decision_D",
    "estado": "estado_2da",
    "actualiz": "updated_at",
    "visita": "fecha_v2",
    "coord": "coordinador_asignado__username",
    "equipo": "equipo_ord",
}

CR_SORT_LABELS: tuple[tuple[str, str], ...] = (
    ("id", "ID"),
    ("edificio", "Edificio"),
    ("score", "Score"),
    ("decision", "Decisión"),
    ("estado", "Estado"),
    ("actualiz", "Última act."),
    ("visita", "Visita"),
    ("coord", "Coordinador"),
    ("equipo", "Equipo"),
)

# Columnas de fecha: el primer clic ordena de más reciente → más antigua
_CR_SORT_DEFAULT_DESC = frozenset({"actualiz", "visita", "score", "id"})


def _cr_build_sort_links(get, orden: str, direccion: str) -> list[dict]:
    """Enlaces de ordenación por columna, preservando filtros cr_/ra_."""
    base_params = [
        (k, v)
        for k, v in (_params_with_prefix(get, "cr_") + _params_with_prefix(get, "ra_"))
        if k not in ("cr_orden", "cr_dir", "cr_page")
    ]
    links: list[dict] = []
    for key, label in CR_SORT_LABELS:
        if key == orden:
            next_dir = "desc" if direccion == "asc" else "asc"
            arrow = "▲" if direccion == "asc" else "▼"
            active = True
        else:
            next_dir = "desc" if key in _CR_SORT_DEFAULT_DESC else "asc"
            arrow = ""
            active = False
        params = list(base_params)
        params.append(("cr_orden", key))
        params.append(("cr_dir", next_dir))
        links.append(
            {
                "key": key,
                "label": label,
                "url": f"/admin/?{urlencode(params)}#casos-recientes",
                "arrow": arrow,
                "active": active,
                "dir": direccion if active else "",
            }
        )
    return links


def get_casos_recientes_context(request, base_qs: QuerySet, titulo: str) -> dict:
    """
    Casos recientes con filtros GET:
    cr_equipo, cr_coord, cr_decision, cr_estado, cr_fecha_desde, cr_fecha_hasta, cr_fecha_campo,
    cr_q (búsqueda genérica), cr_orden, cr_dir.
    Por defecto: orden por última actualización (más reciente primero).
    """
    from django.db.models import F, Value
    from django.db.models.functions import Coalesce, Lower

    viewer = getattr(getattr(request, "user", None), "is_authenticated", False)
    viewer_user = request.user if request and viewer else None

    get = getattr(request, "GET", {}) if request else {}
    f_equipo = (get.get("cr_equipo") or "").strip()
    f_coord = (get.get("cr_coord") or "").strip()
    f_decision = (get.get("cr_decision") or "").strip()
    f_estado = (get.get("cr_estado") or "").strip()
    f_desde = (get.get("cr_fecha_desde") or "").strip()
    f_hasta = (get.get("cr_fecha_hasta") or "").strip()
    f_campo = (get.get("cr_fecha_campo") or "actualizacion").strip()
    f_q = (get.get("cr_q") or "").strip()
    if f_campo not in ("visita", "actualizacion"):
        f_campo = "actualizacion"

    f_orden = (get.get("cr_orden") or "actualiz").strip()
    f_dir = (get.get("cr_dir") or "desc").strip().lower()
    if f_orden not in CR_SORT_FIELDS:
        f_orden = "actualiz"
    if f_dir not in ("asc", "desc"):
        f_dir = "desc"

    qs = base_qs.select_related(
        "coordinador_asignado", "inspector_asignado", "revisor_asignado"
    )

    if f_equipo.isdigit():
        qs = _filtrar_qs_por_equipo(qs, f_equipo)
    if f_coord.isdigit():
        qs = qs.filter(coordinador_asignado_id=int(f_coord))
    if f_decision:
        qs = qs.filter(decision_D=f_decision)
    if f_estado:
        qs = qs.filter(estado_2da=f_estado)
    if f_q:
        qs = _filtrar_casos_por_q(qs, f_q)

    d_desde = _parse_ymd(f_desde)
    d_hasta = _parse_ymd(f_hasta)
    if f_campo == "actualizacion":
        if d_desde:
            qs = qs.filter(updated_at__date__gte=d_desde)
        if d_hasta:
            qs = qs.filter(updated_at__date__lte=d_hasta)
    else:
        if d_desde:
            qs = qs.filter(fecha_v2__gte=d_desde)
        if d_hasta:
            qs = qs.filter(fecha_v2__lte=d_hasta)

    qs = qs.annotate(
        edificio_ord=Coalesce("nombre_conf", "nombre_hab", Value("")),
        equipo_ord=Coalesce(
            "coordinador_asignado__username",
            "inspector_asignado__username",
            Value(""),
        ),
    )

    field = CR_SORT_FIELDS[f_orden]
    # Texto: orden case-insensitive cuando aplica
    if f_orden in ("edificio", "coord", "equipo", "decision", "estado"):
        if f_dir == "desc":
            qs = qs.order_by(Lower(field).desc(), "-updated_at")
        else:
            qs = qs.order_by(Lower(field).asc(), "-updated_at")
    elif f_orden == "visita":
        # Sin fecha de visita al final, no arriba
        expr = F("fecha_v2").desc(nulls_last=True) if f_dir == "desc" else F("fecha_v2").asc(nulls_last=True)
        qs = qs.order_by(expr, "-updated_at")
    else:
        prefix = "-" if f_dir == "desc" else ""
        qs = qs.order_by(f"{prefix}{field}", "-updated_at")

    activo = bool(
        f_equipo
        or f_coord
        or f_decision
        or f_estado
        or f_desde
        or f_hasta
        or f_q
        or f_campo != "actualizacion"
        or f_orden != "actualiz"
        or f_dir != "desc"
    )
    total = qs.count()
    paginator = Paginator(qs, CR_PAGE_SIZE)
    try:
        page_n = int((get.get("cr_page") or "1").strip() or "1")
    except (TypeError, ValueError):
        page_n = 1
    try:
        page_obj = paginator.page(page_n)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    recientes = list(page_obj.object_list)
    for caso in recientes:
        uname = ""
        if caso.coordinador_asignado_id:
            uname = caso.coordinador_asignado.username or ""
        elif caso.inspector_asignado_id:
            uname = caso.inspector_asignado.username or ""
        eq = equipo_de_username(uname)
        caso.equipo_label = etiqueta_equipo(eq) if eq else "—"

    viewer_lists = (
        viewer_user
        if viewer_user and es_solo_coordinador(viewer_user) and not es_administrador(viewer_user)
        else None
    )
    coordinadores = list(usuarios_por_rol(viewer_lists)["coordinadores"])

    return {
        "dashboard_recientes": recientes,
        "dashboard_titulo_recientes": titulo,
        "cr_total": total,
        "cr_paginacion": _page_links(
            get=get,
            page_param="cr_page",
            page_obj=page_obj,
            keep_prefixes=("cr_", "ra_"),
            anchor="casos-recientes",
        ),
        "cr_filtros": {
            "equipo": f_equipo,
            "coord": f_coord,
            "decision": f_decision,
            "estado": f_estado,
            "fecha_desde": f_desde,
            "fecha_hasta": f_hasta,
            "fecha_campo": f_campo,
            "q": f_q,
            "orden": f_orden,
            "dir": f_dir,
        },
        "cr_equipos": equipos_con_etiqueta(),
        "cr_coordinadores": coordinadores,
        "cr_decisiones": list(ch.DecisionD.choices),
        "cr_estados": list(ch.Estado2daRonda.choices),
        "cr_activo": activo,
        "cr_sort_links": _cr_build_sort_links(get, f_orden, f_dir),
    }


def _equipos_disponibles() -> list[str]:
    """Números de brigada/equipo presentes en usernames coord./ing.equipoN."""
    nums: set[str] = set()
    qs = User.objects.filter(is_active=True).filter(
        Q(username__istartswith="coord.equipo") | Q(username__istartswith="ing.equipo")
    ).values_list("username", flat=True)
    for username in qs:
        eq = equipo_de_username(username)
        if eq:
            nums.add(eq)
    return sorted(nums, key=lambda x: int(x) if x.isdigit() else 0)


def _caso_pks_por_equipo(equipo: str) -> list[str]:
    pref_coord = f"coord.equipo{equipo}"
    pref_ing = f"ing.equipo{equipo}."
    pks = (
        CasoRojo.objects.filter(
            Q(coordinador_asignado__username__iexact=pref_coord)
            | Q(coordinador_asignado__username__istartswith=f"{pref_coord}.")
            | Q(inspector_asignado__username__istartswith=pref_ing)
        )
        .values_list("pk", flat=True)
    )
    return [str(pk) for pk in pks]


def get_recent_actions_context(request=None) -> dict:
    """
    Acciones recientes (LogEntry de Casos ROJO) con filtros GET:
    ra_equipo, ra_coord, ra_actor, ra_tipo, ra_dias, ra_q (búsqueda genérica).
    """
    empty = {
        "ra_entries": [],
        "ra_total": 0,
        "ra_paginacion": None,
        "ra_filtros": {
            "equipo": "",
            "coord": "",
            "actor": "",
            "tipo": "",
            "dias": "14",
            "q": "",
        },
        "ra_equipos": [],
        "ra_coordinadores": [],
        "ra_actores": [],
        "ra_activo": False,
        "ra_alcance_restringido": False,
    }
    if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
        return empty

    get = request.GET
    f_equipo = (get.get("ra_equipo") or "").strip()
    f_coord = (get.get("ra_coord") or "").strip()
    f_actor = (get.get("ra_actor") or "").strip()
    f_tipo = (get.get("ra_tipo") or "").strip()
    f_dias = (get.get("ra_dias") or "14").strip()
    f_q = (get.get("ra_q") or "").strip()

    ct = ContentType.objects.get_for_model(CasoRojo)
    qs = LogEntry.objects.filter(content_type=ct).select_related("user", "content_type")

    # Alcance por rol: coord./ingeniero solo ven log de SUS casos (no el inventario global).
    # Admin, revisor y consulta sí ven todas las acciones.
    user = request.user
    bolsa_ids: list[str] | None = None
    if not ve_todos_los_casos(user) and not es_administrador(user):
        bolsa_ids = [
            str(pk) for pk in filtrar_casos_por_rol(user).values_list("pk", flat=True)
        ]
        qs = qs.filter(object_id__in=bolsa_ids)

    if f_dias.isdigit() and int(f_dias) > 0:
        since = timezone.now() - timedelta(days=int(f_dias))
        qs = qs.filter(action_time__gte=since)

    if f_tipo == "add":
        qs = qs.filter(action_flag=ADDITION)
    elif f_tipo == "change":
        qs = qs.filter(action_flag=CHANGE)
    elif f_tipo == "delete":
        qs = qs.filter(action_flag=DELETION)

    if f_actor.isdigit():
        qs = qs.filter(user_id=int(f_actor))

    # Filtros de brigada/coord solo tienen sentido dentro del alcance del usuario
    if f_coord.isdigit():
        caso_ids = CasoRojo.objects.filter(
            coordinador_asignado_id=int(f_coord)
        ).values_list("pk", flat=True)
        if bolsa_ids is not None:
            caso_ids = [pk for pk in caso_ids if str(pk) in set(bolsa_ids)]
        qs = qs.filter(object_id__in=[str(pk) for pk in caso_ids])

    if f_equipo.isdigit():
        eq_ids = _caso_pks_por_equipo(f_equipo)
        if bolsa_ids is not None:
            eq_ids = [pk for pk in eq_ids if pk in set(bolsa_ids)]
        qs = qs.filter(object_id__in=eq_ids)

    if f_q:
        qs = _filtrar_log_por_q(qs, f_q)

    qs = qs.order_by("-action_time")
    total = qs.count()
    paginator = Paginator(qs, RA_PAGE_SIZE)
    try:
        page_n = int((get.get("ra_page") or "1").strip() or "1")
    except (TypeError, ValueError):
        page_n = 1
    try:
        page_obj = paginator.page(page_n)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    entries = list(page_obj.object_list)

    # Listas de filtros: limitar a su alcance (coord/ingeniero)
    alcance_restringido = bolsa_ids is not None
    viewer_lists = user if (alcance_restringido and es_solo_coordinador(user)) else None
    por_rol = usuarios_por_rol(viewer_lists)
    coordinadores = list(por_rol["coordinadores"])

    since_actores = timezone.now() - timedelta(days=30)
    actores_qs = LogEntry.objects.filter(
        content_type=ct, action_time__gte=since_actores
    )
    if bolsa_ids is not None:
        actores_qs = actores_qs.filter(object_id__in=bolsa_ids)
    actor_ids = actores_qs.values_list("user_id", flat=True).distinct()
    actores = list(
        User.objects.filter(pk__in=actor_ids, is_active=True).order_by("username")[:80]
    )

    equipos = equipos_con_etiqueta()
    if alcance_restringido and es_solo_inspector(user):
        equipos = []
        coordinadores = []
    elif alcance_restringido and es_solo_coordinador(user):
        from inspecciones.asignacion import equipo_de_username as _eq

        eq_self = _eq(user.username or "")
        if eq_self:
            equipos = [e for e in equipos if e.get("numero") == eq_self]
        else:
            equipos = []

    activo = bool(
        f_equipo or f_coord or f_actor or f_tipo or f_q or (f_dias and f_dias != "14")
    )

    return {
        "ra_entries": entries,
        "ra_total": total,
        "ra_paginacion": _page_links(
            get=get,
            page_param="ra_page",
            page_obj=page_obj,
            keep_prefixes=("cr_", "ra_"),
            anchor="acciones-recientes",
        ),
        "ra_filtros": {
            "equipo": f_equipo,
            "coord": f_coord,
            "actor": f_actor,
            "tipo": f_tipo,
            "dias": f_dias,
            "q": f_q,
        },
        "ra_equipos": equipos,
        "ra_coordinadores": coordinadores,
        "ra_actores": actores,
        "ra_activo": activo,
        "ra_alcance_restringido": alcance_restringido,
    }


def patch_admin_index() -> None:
    original = admin.site.index

    def index(request, extra_context=None):
        ctx = extra_context or {}
        ctx.update(get_dashboard_context(request))
        return original(request, ctx)

    admin.site.index = index
