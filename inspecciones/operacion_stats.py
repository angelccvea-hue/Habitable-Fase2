"""Agregaciones para el Dashboard de operación diaria (bandeja equipos)."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from inspecciones import choices as ch
from inspecciones.admin_dashboard import _filtrar_qs_por_equipo
from inspecciones.asignacion import equipos_con_etiqueta, etiqueta_equipo
from inspecciones.choices import COMPLEMENTO_LABELS, parse_complementos
from inspecciones.models import HistorialEstado
from inspecciones.workflow import MIN_CROQUIS_CIERRE, MIN_FOTOS_CIERRE, filtrar_casos_por_rol

# Orden operativo del embudo (para ejes)
_ORDEN_ESTADO = [
    ch.Estado2daRonda.PENDIENTE,
    ch.Estado2daRonda.EN_VISITA,
    ch.Estado2daRonda.BORRADOR,
    ch.Estado2daRonda.PENDIENTE_REVISION,
    ch.Estado2daRonda.REVISADO,
    ch.Estado2daRonda.APROBADO,
    ch.Estado2daRonda.PUBLICADO,
]

_DEC_KEYS = ("D1", "D2", "D3", "D4")


def qs_bandeja_equipos(qs):
    """Solo casos asignados a brigadas (coord.equipo* / ing.equipo*)."""
    return qs.filter(
        Q(coordinador_asignado__username__istartswith="coord.equipo")
        | Q(inspector_asignado__username__istartswith="ing.equipo")
    )


def _parse_ymd(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _label_decision(val) -> str:
    raw = getattr(val, "value", val)
    raw = (str(raw) if raw is not None else "").strip()
    if not raw or raw == ch.DecisionD.PENDIENTE:
        return "Sin dictamen"
    return (raw.split("—")[0].split("-")[0]).strip() or raw


def _label_estado(val) -> str:
    raw = getattr(val, "value", val)
    raw = (str(raw) if raw is not None else "").strip()
    return raw or "Sin estado"


def _pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 1) if total else 0.0


def _q_sin_dictamen() -> Q:
    return Q(decision_D="") | Q(decision_D=ch.DecisionD.PENDIENTE)


def _decision_counts(qs) -> dict[str, int]:
    """Conteo D1–D4 (ignora sin dictamen)."""
    out = {k: 0 for k in _DEC_KEYS}
    for r in qs.values("decision_D").annotate(n=Count("id")):
        lab = _label_decision(r["decision_D"] or "")
        if lab in out:
            out[lab] += int(r["n"])
    return out


def _dias_sin_actualizar(updated_at) -> int:
    """Días naturales desde la última actualización del caso (0 si hoy / sin fecha)."""
    if not updated_at:
        return 999
    if timezone.is_aware(updated_at):
        d = timezone.localtime(updated_at).date()
    elif isinstance(updated_at, datetime):
        d = updated_at.date()
    elif isinstance(updated_at, date):
        d = updated_at
    else:
        return 999
    return max(0, (timezone.localdate() - d).days)


def _clase_antiguedad(dias: int) -> str:
    """Color por días sin cambios: fresco → crítico."""
    if dias >= 15:
        return "op-case-crit"
    if dias >= 8:
        return "op-case-alta"
    if dias >= 4:
        return "op-case-media"
    return "op-case-ok"


def _muestras(qs, *, limite: int = 500) -> list[dict[str, Any]]:
    """Lista de casos de la alerta, ordenados por más días sin actualizar primero."""
    rows = list(
        qs.values("pk", "hab_id", "nombre_hab", "score", "updated_at")[:limite]
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        dias = _dias_sin_actualizar(r.get("updated_at"))
        out.append(
            {
                "pk": r["pk"],
                "hab_id": r["hab_id"],
                "nombre": (r["nombre_hab"] or "")[:48],
                "score": r["score"],
                "url": f"/admin/inspecciones/casorojo/{r['pk']}/change/",
                "dias_sin_actualizar": dias,
                "clase_antiguedad": _clase_antiguedad(dias),
                "titulo_antiguedad": (
                    f"{dias} día{'s' if dias != 1 else ''} sin actualizar"
                    if dias < 999
                    else "Sin fecha de actualización"
                ),
            }
        )
    out.sort(key=lambda m: (-m["dias_sin_actualizar"], m["hab_id"] or 0))
    return out


def _build_alertas_dictamen(qs) -> list[dict[str, Any]]:
    """Calidad de dictamen: listas accionables con conteo y muestra."""
    hoy = timezone.localdate()
    alertas: list[dict[str, Any]] = []

    def add(codigo: str, titulo: str, severidad: str, sub_qs, ayuda: str = "") -> None:
        n = sub_qs.count()
        if n <= 0:
            return
        alertas.append(
            {
                "codigo": codigo,
                "titulo": titulo,
                "severidad": severidad,
                "n": n,
                "ayuda": ayuda,
                "muestras": _muestras(sub_qs),
            }
        )

    add(
        "visita_sin_d",
        "Con visita 2 y sin dictamen",
        "warn",
        qs.filter(fecha_v2__isnull=False).filter(_q_sin_dictamen()),
        "Cerrar dictamen D o devolver a campo si falta evidencia.",
    )
    add(
        "d1_sin_comp",
        "D1 sin código de complemento",
        "danger",
        qs.filter(decision_D__istartswith="D1").filter(
            Q(complementos_D="") | Q(complementos_D__isnull=True)
        ),
        "Indicar GEO/ENS/MOD/… en complementos.",
    )
    add(
        "d1_sin_plazo",
        "D1 sin plazo de complemento",
        "warn",
        qs.filter(decision_D__istartswith="D1").filter(complemento_plazo__isnull=True),
        "Definir fecha objetivo / reinspección.",
    )
    add(
        "d1_plazo_vencido",
        "D1 con plazo vencido",
        "danger",
        qs.filter(decision_D__istartswith="D1").filter(complemento_plazo__lt=hoy),
        "Revisar cumplimiento del complemento.",
    )
    add(
        "d2_sin_mag",
        "D2 sin magnitud M1–M4",
        "warn",
        qs.filter(decision_D__istartswith="D2").filter(
            Q(magnitud_M="")
            | Q(magnitud_M=ch.MagnitudM.PENDIENTE)
            | Q(magnitud_M=ch.MagnitudM.NA)
        ),
        "Asignar magnitud de reparación/reconstrucción.",
    )
    add(
        "d34_score_bajo",
        "D3/D4 con score bajo (< 40)",
        "warn",
        qs.filter(
            Q(decision_D__istartswith="D3") | Q(decision_D__istartswith="D4")
        ).filter(score__isnull=False, score__lt=40),
        "Validar consistencia dictamen vs score de gravedad.",
    )
    add(
        "d34_sin_vol",
        "D3/D4 sin volumen de escombros (m³)",
        "warn",
        qs.filter(
            Q(decision_D__istartswith="D3") | Q(decision_D__istartswith="D4")
        ).filter(vol_escombros_m3__isnull=True),
        "Completar estimación de escombros (relevante para demolición / colapso).",
    )
    add(
        "d34_sin_medidas",
        "D3/D4 sin medidas inmediatas",
        "danger",
        qs.filter(
            Q(decision_D__istartswith="D3") | Q(decision_D__istartswith="D4")
        ).filter(Q(medidas="") | Q(medidas__isnull=True)),
        "Registrar perímetro, desalojo u otras medidas de control.",
    )
    # Evidencia: solo casos con visita 2 (ya en campo); evita ruido de pend. verificación
    con_visita = qs.filter(fecha_v2__isnull=False)
    add(
        "fotos_insuficientes",
        f"Con visita 2 y menos de {MIN_FOTOS_CIERRE} fotos",
        "danger",
        con_visita.annotate(_n_fotos=Count("fotos")).filter(
            _n_fotos__lt=MIN_FOTOS_CIERRE
        ),
        f"Adjuntar al menos {MIN_FOTOS_CIERRE} fotografías de evidencia (requisito para elevar/PDF).",
    )
    add(
        "sin_croquis",
        "Con visita 2 y sin croquis",
        "danger",
        con_visita.annotate(_n_croquis=Count("croquis")).filter(
            _n_croquis__lt=MIN_CROQUIS_CIERRE
        ),
        f"Adjuntar al menos {MIN_CROQUIS_CIERRE} croquis (requisito para elevar).",
    )
    return alertas


def _d1_por_complemento(qs) -> list[dict[str, Any]]:
    d1 = qs.filter(decision_D__istartswith="D1")
    n_d1 = d1.count()
    counter: Counter[str] = Counter()
    for raw in d1.values_list("complementos_D", flat=True):
        codes = parse_complementos(raw or "")
        if not codes:
            counter["(sin código)"] += 1
        else:
            for code in codes:
                counter[code] += 1
    rows = []
    for code, n in counter.most_common():
        label = COMPLEMENTO_LABELS.get(code, code)
        if code == "(sin código)":
            label = "Sin código"
            short = "Sin cód."
        else:
            short = code
        rows.append(
            {
                "code": code,
                "name": short,
                "name_full": label,
                "value": n,
                "pct": _pct(n, n_d1),
            }
        )
    return rows


def _d2_por_magnitud(qs) -> list[dict[str, Any]]:
    d2 = qs.filter(decision_D__istartswith="D2")
    n_d2 = d2.count()
    orden = [c.value for c in ch.MagnitudM]
    raw = {
        (r["magnitud_M"] or ""): r["n"]
        for r in d2.values("magnitud_M").annotate(n=Count("id"))
    }
    rows = []
    for key in orden:
        n = int(raw.pop(key, 0))
        if not n:
            continue
        short = (key.split("—")[0].strip() if key else "—") or "—"
        rows.append({"name": short, "name_full": key or "—", "value": n, "pct": _pct(n, n_d2)})
    for key, n in sorted(raw.items(), key=lambda x: -x[1]):
        if not n:
            continue
        short = (key.split("—")[0].strip() if key else "Sin magnitud") or "Sin magnitud"
        rows.append({"name": short or "Sin magnitud", "name_full": key or "—", "value": n, "pct": _pct(n, n_d2)})
    return rows


def _q_d34() -> Q:
    return Q(decision_D__istartswith="D3") | Q(decision_D__istartswith="D4")


def _d34_panel(qs) -> dict[str, Any]:
    """Analítica D3 (demoler) + D4 (escombros): volumen, score, prioridad."""
    d34 = qs.filter(_q_d34())
    n = d34.count()
    n_d3 = qs.filter(decision_D__istartswith="D3").count()
    n_d4 = qs.filter(decision_D__istartswith="D4").count()
    agg = d34.aggregate(
        vol_suma=Sum("vol_escombros_m3"),
        vol_prom=Avg("vol_escombros_m3"),
        score_prom=Avg("score"),
        n_con_vol=Count("id", filter=Q(vol_escombros_m3__isnull=False)),
        n_con_score=Count("id", filter=Q(score__isnull=False)),
    )
    vol_tramos = [
        {
            "name": "Sin dato",
            "value": d34.filter(vol_escombros_m3__isnull=True).count(),
        },
        {
            "name": "< 50 m³",
            "value": d34.filter(vol_escombros_m3__lt=50).count(),
        },
        {
            "name": "50–200 m³",
            "value": d34.filter(
                vol_escombros_m3__gte=50, vol_escombros_m3__lt=200
            ).count(),
        },
        {
            "name": "> 200 m³",
            "value": d34.filter(vol_escombros_m3__gte=200).count(),
        },
    ]
    for row in vol_tramos:
        row["pct"] = _pct(row["value"], n)

    score_tramos = [
        {"name": "Sin score", "value": d34.filter(score__isnull=True).count()},
        {
            "name": "0–39",
            "value": d34.filter(score__isnull=False, score__lt=40).count(),
        },
        {
            "name": "40–69",
            "value": d34.filter(score__gte=40, score__lt=70).count(),
        },
        {
            "name": "70–100",
            "value": d34.filter(score__gte=70).count(),
        },
    ]
    for row in score_tramos:
        row["pct"] = _pct(row["value"], n)

    prio_raw = {
        (r["prioridad"] or "") or "—": r["n"]
        for r in d34.values("prioridad").annotate(n=Count("id"))
    }
    prio_orden = [c.value for c in ch.PrioridadOperativa] + ["—"]
    prioridades = []
    seen: set[str] = set()
    for key in prio_orden:
        if key in seen:
            continue
        nn = int(prio_raw.pop(key, 0))
        if not nn and key == "—":
            continue
        if nn:
            seen.add(key)
            prioridades.append(
                {
                    "name": key if key != "—" else "Sin prioridad",
                    "value": nn,
                    "pct": _pct(nn, n),
                }
            )
    for key, nn in sorted(prio_raw.items(), key=lambda x: -x[1]):
        if nn:
            prioridades.append(
                {
                    "name": key or "Sin prioridad",
                    "value": int(nn),
                    "pct": _pct(int(nn), n),
                }
            )

    return {
        "n": n,
        "n_d3": n_d3,
        "n_d4": n_d4,
        "vol_suma_m3": round(float(agg["vol_suma"] or 0), 1),
        "vol_prom_m3": round(float(agg["vol_prom"] or 0), 1),
        "n_con_vol": int(agg["n_con_vol"] or 0),
        "score_prom": round(float(agg["score_prom"] or 0), 1),
        "n_con_score": int(agg["n_con_score"] or 0),
        "vol_tramos": vol_tramos,
        "score_tramos": score_tramos,
        "prioridades": prioridades,
    }


def _embudo_dictamen(qs) -> dict[str, Any]:
    """Embudo operativo + desglose por D en etapas clave."""
    total = qs.count()
    con_visita = qs.filter(fecha_v2__isnull=False).count()
    con_dictamen = qs.exclude(_q_sin_dictamen()).count()
    cola = qs.filter(estado_2da__in=ch.ESTADOS_COLA_REVISION).count()
    aprobado = qs.filter(
        estado_2da__in=(ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.PUBLICADO)
    ).count()
    pasos = [
        {"name": "Bandeja", "value": total, "pct": _pct(total, total)},
        {"name": "Con visita", "value": con_visita, "pct": _pct(con_visita, total)},
        {"name": "Con dictamen", "value": con_dictamen, "pct": _pct(con_dictamen, total)},
        {"name": "Cola revisión", "value": cola, "pct": _pct(cola, total)},
        {"name": "Aprobado+", "value": aprobado, "pct": _pct(aprobado, total)},
    ]
    por_d = []
    for d in _DEC_KEYS:
        dqs = qs.filter(decision_D__istartswith=d)
        nn = dqs.count()
        por_d.append(
            {
                "d": d,
                "total": nn,
                "borrador": dqs.filter(estado_2da=ch.Estado2daRonda.BORRADOR).count(),
                "cola": dqs.filter(estado_2da__in=ch.ESTADOS_COLA_REVISION).count(),
                "aprobado": dqs.filter(
                    estado_2da__in=(
                        ch.Estado2daRonda.APROBADO,
                        ch.Estado2daRonda.PUBLICADO,
                    )
                ).count(),
                "campo": dqs.filter(
                    estado_2da__in=(
                        ch.Estado2daRonda.PENDIENTE,
                        ch.Estado2daRonda.EN_VISITA,
                    )
                ).count(),
            }
        )
    return {
        "pasos": pasos,
        "por_d": por_d,
        "sin_dictamen": qs.filter(_q_sin_dictamen()).count(),
    }


def _ritmo_dictamenes(qs, *, d_desde: date, d_hasta: date) -> dict[str, Any]:
    """
    Dictámenes asociados a visita en la ventana (fecha_v2) + acumulado.
    Proxy operativo: casos ya dictaminados cuya visita 2 cayó en el lapso.
    """
    rows = (
        qs.exclude(_q_sin_dictamen())
        .filter(fecha_v2__gte=d_desde, fecha_v2__lte=d_hasta)
        .values("fecha_v2")
        .annotate(n=Count("id"))
        .order_by("fecha_v2")
    )
    mapa = {r["fecha_v2"]: int(r["n"]) for r in rows if r["fecha_v2"]}
    dias: list[str] = []
    serie: list[int] = []
    acum: list[int] = []
    run = 0
    cur = d_desde
    while cur <= d_hasta:
        dias.append(cur.isoformat())
        v = int(mapa.get(cur, 0))
        serie.append(v)
        run += v
        acum.append(run)
        cur += timedelta(days=1)
    return {"dias": dias, "serie": serie, "acum": acum, "total_ventana": run}


def _q_la_guaira() -> Q:
    """Municipio/parroquia o dirección típicos de La Guaira (ex Vargas)."""
    return (
        Q(muni_parr__icontains="vargas")
        | Q(muni_parr__icontains="guaira")
        | Q(muni_parr__icontains="guaíra")
        | Q(muni_parr__icontains="macuto")
        | Q(muni_parr__icontains="caraballeda")
        | Q(muni_parr__icontains="urimare")
        | Q(muni_parr__icontains="catia la mar")
        | Q(direccion_hab__icontains="la guaira")
        | Q(direccion_hab__icontains="vargas")
    )


def _q_caracas() -> Q:
    """Distrito Capital / municipios del AMM (sin confundir con ranking 'Nacional')."""
    return (
        Q(muni_parr__icontains="libertador")
        | Q(muni_parr__icontains="chacao")
        | Q(muni_parr__icontains="baruta")
        | Q(muni_parr__icontains="hatillo")
        | Q(muni_parr__icontains="sucre")
        | Q(muni_parr__icontains="caracas")
        | Q(muni_parr__icontains="distrito capital")
        | Q(direccion_hab__icontains="caracas")
        | Q(direccion_hab__icontains="distrito capital")
    )


def _agg_estado_decision(qs) -> dict[str, Any]:
    total = qs.count()
    por_estado_raw = {
        (r["estado_2da"] or ""): r["n"]
        for r in qs.values("estado_2da").annotate(n=Count("id"))
    }
    por_estado = []
    for est in _ORDEN_ESTADO:
        n = int(por_estado_raw.pop(est, 0))
        if n:
            por_estado.append(
                {"name": _label_estado(est), "value": n, "pct": _pct(n, total)}
            )
    for est, n in sorted(por_estado_raw.items(), key=lambda x: -x[1]):
        if n:
            por_estado.append(
                {"name": _label_estado(est), "value": n, "pct": _pct(n, total)}
            )

    dec_counter: Counter[str] = Counter()
    for r in qs.values("decision_D").annotate(n=Count("id")):
        dec_counter[_label_decision(r["decision_D"] or "")] += r["n"]
    por_decision = [
        {"name": k, "value": v, "pct": _pct(v, total)}
        for k, v in dec_counter.most_common()
    ]
    return {"total": total, "por_estado": por_estado, "por_decision": por_decision}


def filtrar_qs_operacion(user, get=None):
    """
    Universo del BI Operación: bandeja de equipos + rol + filtros GET.
    Filtros: equipo, estado, decision, zona (guaira|caracas).
    """
    get = get or {}
    qs = qs_bandeja_equipos(filtrar_casos_por_rol(user))

    f_equipo = (get.get("equipo") or "").strip()
    if f_equipo.isdigit():
        qs = _filtrar_qs_por_equipo(qs, f_equipo)

    f_estado = (get.get("estado") or "").strip()
    if f_estado:
        qs = qs.filter(estado_2da=f_estado)

    f_decision = (get.get("decision") or "").strip()
    if f_decision == "sin":
        qs = qs.filter(Q(decision_D="") | Q(decision_D=ch.DecisionD.PENDIENTE))
    elif f_decision:
        # Prefijo D1/D2/… o valor completo
        qs = qs.filter(decision_D__istartswith=f_decision)

    f_zona = (get.get("zona") or "").strip().lower()
    if f_zona in ("guaira", "la_guaira", "la-guaira"):
        qs = qs.filter(_q_la_guaira())
    elif f_zona == "caracas":
        qs = qs.filter(_q_caracas()).exclude(_q_la_guaira())

    f_visita = (get.get("visita") or "").strip()
    if f_visita == "1":
        qs = qs.filter(fecha_v2__isnull=False)
    elif f_visita == "0":
        qs = qs.filter(fecha_v2__isnull=True)

    return qs


def build_operacion_stats(user, *, get=None) -> dict[str, Any]:
    """
    Stats orientadas a interpretar avance de bandeja (no altas masivas al sistema).
    """
    get = get or {}
    qs = filtrar_qs_operacion(user, get)

    f_equipo = (get.get("equipo") or "").strip()
    f_estado = (get.get("estado") or "").strip()
    f_decision = (get.get("decision") or "").strip()
    f_zona = (get.get("zona") or "").strip().lower()
    f_visita = (get.get("visita") or "").strip()

    hoy = timezone.localdate()
    # Lapso parametrizable: ?dias=7|14|30 (default 14) o desde/hasta explícitos
    preset_dias = (get.get("dias") or "").strip()
    if preset_dias.isdigit() and int(preset_dias) in (7, 14, 30):
        n_preset = int(preset_dias)
        d_hasta = hoy
        d_desde = hoy - timedelta(days=n_preset - 1)
    else:
        n_preset = 14
        d_desde = _parse_ymd(get.get("desde") or "") or (hoy - timedelta(days=13))
        d_hasta = _parse_ymd(get.get("hasta") or "") or hoy
        if not (get.get("desde") or get.get("hasta")):
            # Sin fechas: default 14 días
            d_desde = hoy - timedelta(days=13)
            d_hasta = hoy
        span = (d_hasta - d_desde).days + 1
        if span in (7, 14, 30):
            n_preset = span

    if d_desde > d_hasta:
        d_desde, d_hasta = d_hasta, d_desde

    dt_desde = timezone.make_aware(datetime.combine(d_desde, datetime.min.time()))
    dt_hasta = timezone.make_aware(datetime.combine(d_hasta, datetime.max.time()))

    total = qs.count()
    con_visita = qs.filter(fecha_v2__isnull=False).count()
    sin_visita = total - con_visita
    sin_dictamen = qs.filter(_q_sin_dictamen()).count()
    con_dictamen = total - sin_dictamen
    cola_revision = qs.filter(estado_2da__in=ch.ESTADOS_COLA_REVISION).count()
    aprobados = qs.filter(
        estado_2da__in=(ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.PUBLICADO)
    ).count()
    borrador = qs.filter(estado_2da=ch.Estado2daRonda.BORRADOR).count()
    en_visita = qs.filter(estado_2da=ch.Estado2daRonda.EN_VISITA).count()
    pendiente = qs.filter(estado_2da=ch.Estado2daRonda.PENDIENTE).count()

    # Ritmo operativo: visitas de campo + llegadas a Revisado (sin created_at)
    visitas_rows = (
        qs.filter(fecha_v2__gte=d_desde, fecha_v2__lte=d_hasta)
        .values("fecha_v2")
        .annotate(n=Count("id"))
        .order_by("fecha_v2")
    )
    visitas_map = {r["fecha_v2"]: r["n"] for r in visitas_rows if r["fecha_v2"]}

    hist_rows = (
        HistorialEstado.objects.filter(
            caso_id__in=qs.values("pk"),
            estado_nuevo__in=ch.ESTADOS_COLA_REVISION,
            created_at__gte=dt_desde,
            created_at__lte=dt_hasta,
        )
        .annotate(d=TruncDate("created_at"))
        .values("d")
        .annotate(n=Count("id"))
        .order_by("d")
    )
    hist_map = {r["d"]: r["n"] for r in hist_rows if r["d"]}

    dias: list[str] = []
    serie_visitas: list[int] = []
    serie_revisados: list[int] = []
    acum_visitas: list[int] = []
    acum_revisados: list[int] = []
    run_v = 0
    run_r = 0
    cur = d_desde
    while cur <= d_hasta:
        dias.append(cur.isoformat())
        v = int(visitas_map.get(cur, 0))
        r = int(hist_map.get(cur, 0))
        serie_visitas.append(v)
        serie_revisados.append(r)
        run_v += v
        run_r += r
        acum_visitas.append(run_v)
        acum_revisados.append(run_r)
        cur += timedelta(days=1)

    # Tortas por zona: Caracas vs La Guaira (sobre la misma bandeja filtrada)
    qs_guaira = qs.filter(_q_la_guaira())
    qs_caracas = qs.filter(_q_caracas()).exclude(_q_la_guaira())
    por_zona = {
        "la_guaira": {"label": "La Guaira", **_agg_estado_decision(qs_guaira)},
        "caracas": {"label": "Caracas", **_agg_estado_decision(qs_caracas)},
    }

    # Por estado (con %) — embudo global bandeja
    por_estado_raw = {
        (r["estado_2da"] or ""): r["n"]
        for r in qs.values("estado_2da").annotate(n=Count("id"))
    }
    por_estado = []
    for est in _ORDEN_ESTADO:
        n = int(por_estado_raw.pop(est, 0))
        if n:
            por_estado.append(
                {"name": _label_estado(est), "value": n, "pct": _pct(n, total)}
            )
    for est, n in sorted(por_estado_raw.items(), key=lambda x: -x[1]):
        if n:
            por_estado.append(
                {"name": _label_estado(est), "value": n, "pct": _pct(n, total)}
            )

    # Por decisión: lista completa + solo dictaminados (para leer D1–D4)
    por_decision_raw = qs.values("decision_D").annotate(n=Count("id")).order_by()
    dec_counter: Counter[str] = Counter()
    for r in por_decision_raw:
        dec_counter[_label_decision(r["decision_D"] or "")] += r["n"]
    por_decision = [
        {"name": k, "value": v, "pct": _pct(v, total)}
        for k, v in dec_counter.most_common()
    ]
    por_decision_dictamen = [
        row for row in por_decision if row["name"] != "Sin dictamen"
    ]
    # % sobre los que sí tienen D
    for row in por_decision_dictamen:
        row["pct_dictamen"] = _pct(row["value"], con_dictamen)

    # Por equipo: composición de estados + % avance
    equipos_opts = equipos_con_etiqueta()
    por_equipo = []
    for item in equipos_opts:
        eq = item["numero"]
        eq_qs = _filtrar_qs_por_equipo(qs, eq)
        n_total = eq_qs.count()
        if n_total == 0:
            continue
        n_visita = eq_qs.filter(fecha_v2__isnull=False).count()
        n_dict = eq_qs.exclude(_q_sin_dictamen()).count()
        estados = {
            "Pendiente verificación": eq_qs.filter(
                estado_2da=ch.Estado2daRonda.PENDIENTE
            ).count(),
            "En visita": eq_qs.filter(estado_2da=ch.Estado2daRonda.EN_VISITA).count(),
            "Borrador": eq_qs.filter(estado_2da=ch.Estado2daRonda.BORRADOR).count(),
            "Pendiente revisión": eq_qs.filter(
                estado_2da=ch.Estado2daRonda.PENDIENTE_REVISION
            ).count(),
            "Revisado": eq_qs.filter(estado_2da=ch.Estado2daRonda.REVISADO).count(),
            "Aprobado+": eq_qs.filter(
                estado_2da__in=(
                    ch.Estado2daRonda.APROBADO,
                    ch.Estado2daRonda.PUBLICADO,
                )
            ).count(),
        }
        decs = _decision_counts(eq_qs)
        por_equipo.append(
            {
                "equipo": etiqueta_equipo(eq),
                "equipo_num": eq,
                "total": n_total,
                "con_visita": n_visita,
                "con_dictamen": n_dict,
                "pct_visita": _pct(n_visita, n_total),
                "pct_dictamen": _pct(n_dict, n_total),
                "estados": estados,
                "decisiones": decs,
                "n_dictamen_d": sum(decs.values()),
            }
        )
    # Orden fijo Equipo 1 … N (arriba→abajo en el BI; no por volumen)
    por_equipo.sort(
        key=lambda x: int(x["equipo_num"])
        if str(x.get("equipo_num", "")).isdigit()
        else 0
    )

    # Decisión × zona (La Guaira / Caracas / Otras)
    qs_otras = qs.exclude(_q_la_guaira()).exclude(_q_caracas())
    decision_x_zona = []
    for label, zqs in (
        ("La Guaira", qs_guaira),
        ("Caracas", qs_caracas),
        ("Otras / sin clasificar", qs_otras),
    ):
        zt = zqs.count()
        if zt == 0:
            continue
        zdec = _decision_counts(zqs)
        zd = sum(zdec.values())
        decision_x_zona.append(
            {
                "zona": label,
                "total": zt,
                "con_dictamen": zd,
                "pct_dictamen": _pct(zd, zt),
                "decisiones": zdec,
            }
        )

    d1_complementos = _d1_por_complemento(qs)
    d2_magnitudes = _d2_por_magnitud(qs)
    d34 = _d34_panel(qs)
    embudo_dictamen = _embudo_dictamen(qs)
    ritmo_dictamenes = _ritmo_dictamenes(qs, d_desde=d_desde, d_hasta=d_hasta)
    n_d1 = qs.filter(decision_D__istartswith="D1").count()
    n_d2 = qs.filter(decision_D__istartswith="D2").count()
    n_d3 = d34["n_d3"]
    n_d4 = d34["n_d4"]
    alertas_dictamen = _build_alertas_dictamen(qs)

    hace_7 = hoy - timedelta(days=6)
    visitas_7 = qs.filter(fecha_v2__gte=hace_7, fecha_v2__lte=hoy).count()
    revisados_7 = HistorialEstado.objects.filter(
        caso_id__in=qs.values("pk"),
        estado_nuevo__in=ch.ESTADOS_COLA_REVISION,
        created_at__date__gte=hace_7,
        created_at__date__lte=hoy,
    ).count()

    n_dias = max((d_hasta - d_desde).days + 1, 1)
    promedio_visitas = round(sum(serie_visitas) / n_dias, 1)

    return {
        "filtros": {
            "equipo": f_equipo,
            "estado": f_estado,
            "decision": f_decision,
            "zona": f_zona,
            "visita": f_visita,
            "desde": d_desde.isoformat(),
            "hasta": d_hasta.isoformat(),
            "dias": n_preset,
            "equipos": equipos_opts,
            "estados": [c[0] for c in ch.Estado2daRonda.choices],
            "decisiones": [
                ("", "Todas"),
                ("sin", "Sin dictamen"),
                ("D1", "D1"),
                ("D2", "D2"),
                ("D3", "D3"),
                ("D4", "D4"),
            ],
            "zonas": [
                ("", "Todas"),
                ("guaira", "La Guaira"),
                ("caracas", "Caracas"),
            ],
            "visitas": [
                ("", "Todas"),
                ("1", "Con visita 2"),
                ("0", "Sin visita 2"),
            ],
        },
        "kpis": {
            "total": total,
            "con_visita": con_visita,
            "sin_visita": sin_visita,
            "sin_dictamen": sin_dictamen,
            "con_dictamen": con_dictamen,
            "cola_revision": cola_revision,
            "aprobados": aprobados,
            "borrador": borrador,
            "en_visita": en_visita,
            "pendiente": pendiente,
            "visitas_7d": visitas_7,
            "revisados_7d": revisados_7,
            "promedio_visitas_dia": promedio_visitas,
            "pct_con_visita": _pct(con_visita, total),
            "pct_con_dictamen": _pct(con_dictamen, total),
            "n_d1": n_d1,
            "n_d2": n_d2,
            "n_d3": n_d3,
            "n_d4": n_d4,
            "n_d34": d34["n"],
            "vol_escombros_m3": d34["vol_suma_m3"],
            "n_alertas": len(alertas_dictamen),
            "n_alertas_casos": sum(a["n"] for a in alertas_dictamen),
            "universo": "bandeja_equipos",
        },
        "ritmo": {
            "dias": dias,
            "visitas": serie_visitas,
            "llegadas_revisado": serie_revisados,
            "acum_visitas": acum_visitas,
            "acum_revisados": acum_revisados,
            "dictamenes": ritmo_dictamenes["serie"],
            "acum_dictamenes": ritmo_dictamenes["acum"],
            "dictamenes_ventana": ritmo_dictamenes["total_ventana"],
        },
        "por_zona": por_zona,
        "por_estado": por_estado,
        "por_decision": por_decision,
        "por_decision_dictamen": por_decision_dictamen,
        "por_equipo": por_equipo,
        "decision_x_zona": decision_x_zona,
        "d1_complementos": d1_complementos,
        "d1_leyenda": [
            {
                "code": c.value,
                "desc": (c.label.split("—", 1)[-1].strip() if "—" in c.label else c.label),
            }
            for c in ch.ComplementoD
        ],
        "d2_magnitudes": d2_magnitudes,
        "d_leyenda": [
            {"code": "D1", "desc": "Complementos requeridos"},
            {"code": "D2", "desc": "Reparar / reconstruir"},
            {"code": "D3", "desc": "Demoler"},
            {"code": "D4", "desc": "Escombros / ya colapsado"},
        ],
        "m_leyenda": [
            {"code": "M1", "desc": "Reparación local (menor)"},
            {"code": "M2", "desc": "Reparación importante"},
            {"code": "M3", "desc": "Reconstrucción parcial"},
            {"code": "M4", "desc": "Reconstrucción / refuerzo mayor"},
        ],
        "d34": d34,
        "embudo_dictamen": embudo_dictamen,
        "alertas_dictamen": alertas_dictamen,
        "dec_keys": list(_DEC_KEYS),
    }
