"""Vista Dashboard de operación diaria (ECharts) + export Excel/PDF."""
from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET

from inspecciones.excel_plantilla import generar_excel_lote
from inspecciones.export_views import _excel_response
from inspecciones.operacion_stats import build_operacion_stats, filtrar_qs_operacion
from inspecciones.workflow import (
    es_administrador,
    es_solo_consulta,
    es_solo_coordinador,
    es_solo_inspector,
    es_solo_revisor,
)

# Tope de filas por descarga (bandeja operativa; evita Excel gigante)
_MAX_EXPORT = 2000


def _rol_alcance(user) -> tuple[str, str]:
    if es_administrador(user):
        return (
            "Administrador",
            "Bandeja de equipos (casos asignados a brigadas; no el inventario completo)",
        )
    if es_solo_consulta(user):
        return "Consulta (solo lectura)", "Inventario completo — sin edición ni asignación"
    if es_solo_coordinador(user):
        return "Coordinador", "Bandeja de su equipo (casos asignados)"
    if es_solo_revisor(user):
        return "Revisor", "Bandeja de equipos (consulta)"
    if es_solo_inspector(user):
        return "Inspector", "Sus casos en bandeja de equipo"
    return "Staff", "Bandeja de equipos según permisos"


def _query_filtros(filtros: dict) -> str:
    """Query string con los filtros activos del dashboard (para botones export)."""
    parts = []
    for key in ("equipo", "estado", "decision", "zona", "visita", "desde", "hasta", "dias"):
        val = filtros.get(key)
        if val is None or val == "":
            continue
        parts.append((key, str(val)))
    return urlencode(parts)


def _spark_polyline(series: list[float | int], *, width: float = 640, height: float = 100) -> str:
    """Convierte serie acumulada en puntos SVG 'x,y x,y …'."""
    if not series:
        return ""
    vals = [float(v or 0) for v in series]
    n = len(vals)
    vmax = max(vals) if vals else 0.0
    if vmax <= 0:
        vmax = 1.0
    pad_y = 6.0
    usable_h = height - 2 * pad_y
    pts = []
    for i, v in enumerate(vals):
        x = 0.0 if n == 1 else (i / (n - 1)) * width
        y = height - pad_y - (v / vmax) * usable_h
        pts.append(f"{x:.1f},{y:.1f}")
    return " ".join(pts)


def _spark_ritmo(stats: dict) -> dict | None:
    ritmo = stats.get("ritmo") or {}
    acum_v = ritmo.get("acum_visitas") or []
    acum_r = ritmo.get("acum_revisados") or []
    acum_d = ritmo.get("acum_dictamenes") or []
    if not (acum_v or acum_r or acum_d):
        return None

    n = max(len(acum_v), len(acum_r), len(acum_d), 1)

    def pad(seq):
        seq = list(seq)
        if len(seq) < n:
            last = seq[-1] if seq else 0
            seq = seq + [last] * (n - len(seq))
        return seq[:n]

    acum_v, acum_r, acum_d = pad(acum_v), pad(acum_r), pad(acum_d)
    return {
        "visitas": _spark_polyline(acum_v),
        "revisados": _spark_polyline(acum_r),
        "dictamenes": _spark_polyline(acum_d),
        "n_dias": n,
    }


def _equipos_pdf_rows(stats: dict) -> list[dict]:
    """Aplana estados con claves con espacios/+/ para la plantilla PDF."""
    rows = []
    for eq in stats.get("por_equipo") or []:
        est = eq.get("estados") or {}
        rows.append(
            {
                "equipo": eq.get("equipo"),
                "total": eq.get("total", 0),
                "pct_visita": eq.get("pct_visita", 0),
                "pct_dictamen": eq.get("pct_dictamen", 0),
                "e_pend": est.get("Pendiente verificación", 0),
                "e_visita": est.get("En visita", 0),
                "e_borrador": est.get("Borrador", 0),
                "e_cola": est.get("Pendiente revisión", 0),
                "e_revisado": est.get("Revisado", 0),
                "e_aprobado": est.get("Aprobado+", 0),
            }
        )
    return rows


def _pct_bar(value: int, total: int) -> float:
    if not total:
        return 0.0
    return round(100.0 * float(value) / float(total), 1)


@staff_member_required
@require_GET
def tablero_operacion(request):
    stats = build_operacion_stats(request.user, get=request.GET)
    rol, alcance = _rol_alcance(request.user)
    filtros = stats["filtros"]
    ctx = {
        "stats": stats,
        "stats_json": json.dumps(stats, cls=DjangoJSONEncoder, ensure_ascii=False),
        "rol_etiqueta": rol,
        "alcance": alcance,
        "filtros": filtros,
        "kpis": stats["kpis"],
        "alertas_dictamen": stats.get("alertas_dictamen") or [],
        "export_qs": _query_filtros(filtros),
    }
    return render(request, "inspecciones/tablero_operacion.html", ctx)


@staff_member_required
@require_GET
def export_operacion_excel(request):
    """
    Descarga Excel (lote, todos los campos de la plantilla) de la bandeja
    filtrada igual que el dashboard de Operación.
    """
    qs = filtrar_qs_operacion(request.user, request.GET).order_by("-score", "hab_id")
    total = qs.count()
    if total == 0:
        return HttpResponseBadRequest(
            "No hay casos con esos filtros en la bandeja de equipos."
        )
    if total > _MAX_EXPORT:
        return HttpResponseBadRequest(
            f"Demasiados casos ({total}). Máximo {_MAX_EXPORT} por descarga; "
            "aplique más filtros (equipo, estado, zona…)."
        )
    casos = list(
        qs.select_related(
            "coordinador_asignado", "inspector_asignado", "revisor_asignado"
        )
    )
    data = generar_excel_lote(casos)
    hoy = date.today().isoformat()
    filename = f"bandeja-operacion-{len(casos)}-casos-{hoy}.xlsx"
    return _excel_response(data, filename)


@staff_member_required
@require_GET
def export_operacion_pdf(request):
    """
    PDF tipo captura del dashboard (opción A): mismos KPIs/filtros +
    barras/resúmenes equivalentes a los gráficos principales.
    """
    stats = build_operacion_stats(request.user, get=request.GET)
    rol, alcance = _rol_alcance(request.user)
    filtros = stats["filtros"]
    html = render_to_string(
        "inspecciones/tablero_operacion_pdf.html",
        {
            "stats": stats,
            "kpis": stats["kpis"],
            "filtros": filtros,
            "alertas_dictamen": stats.get("alertas_dictamen") or [],
            "rol_etiqueta": rol,
            "alcance": alcance,
            "generado": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
            "spark_ritmo": _spark_ritmo(stats),
            "equipos_pdf": _equipos_pdf_rows(stats),
            "d34_n": (stats.get("d34") or {}).get("n") or 0,
        },
    )
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
    filename = f"Dashboard-FaseII-{stamp}.pdf"
    try:
        from weasyprint import HTML as WeasyHTML

        pdf = WeasyHTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
    except Exception:
        # Fallback local (Windows sin libs WeasyPrint): Chromium/Edge headless
        pdf = _pdf_via_edge(html, filename)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


def _pdf_via_edge(html: str, filename: str) -> bytes:
    """Genera PDF con Microsoft Edge headless (desarrollo Windows)."""
    import subprocess
    import tempfile
    from pathlib import Path

    edge_candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge = next((p for p in edge_candidates if p.is_file()), None)
    if not edge:
        raise RuntimeError(
            "No se pudo generar PDF: WeasyPrint no disponible y Edge no encontrado."
        )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "dashboard.html"
        pdf_path = tmp_path / filename
        html_path.write_text(html, encoding="utf-8")
        cmd = [
            str(edge),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not pdf_path.is_file():
            raise RuntimeError(
                f"Edge falló al generar PDF (code={r.returncode}). {r.stderr[:300]}"
            )
        return pdf_path.read_bytes()
