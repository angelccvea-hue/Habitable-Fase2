from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from inspecciones.gps_utils import coordenadas_caso, filtrar_casos_con_gps
from inspecciones.guia_pdf import render_guia_usuario_pdf
from inspecciones.models import CasoRojo, CroquisAdjunto, InformePdfAdjunto
from inspecciones.operacion_stats import qs_bandeja_equipos
from inspecciones.report_sections import build_report_sections
from inspecciones.workflow import (
    FlujoRevision,
    MIN_FOTOS_CIERRE,
    filtrar_casos_por_rol,
    usuario_puede_ver_caso,
    validar_fotos_informe,
)


def _html_to_pdf(html: str, base_url: str, filename: str = "doc.pdf") -> bytes:
    try:
        from weasyprint import HTML

        return HTML(string=html, base_url=base_url).write_pdf()
    except Exception:
        from inspecciones.operacion_views import _pdf_via_edge

        return _pdf_via_edge(html, filename)


def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "proyecto": "CPEH Fase II — Seguimiento ROJO",
            "version": "0.3.0-metrados-anteproyecto",
            "casos": CasoRojo.objects.count(),
            "informes_pdf": InformePdfAdjunto.objects.count(),
            "croquis": CroquisAdjunto.objects.count(),
            "debug": bool(settings.DEBUG),
        }
    )


def caso_rojo_pdf(request, pk: int) -> HttpResponse:
    caso = get_object_or_404(CasoRojo, pk=pk)
    if not usuario_puede_ver_caso(request.user, caso):
        return HttpResponse(status=403)
    try:
        validar_fotos_informe(caso)
    except ValidationError as exc:
        msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        if getattr(request.user, "is_staff", False):
            messages.error(request, msg)
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
            )
        return HttpResponse(msg, status=400, content_type="text/plain; charset=utf-8")
    nombre = caso.nombre_conf or caso.nombre_hab or f"ID {caso.hab_id}"
    fotos_anexo = _fotos_anexo_para_pdf(caso)
    # Doble chequeo: archivos en disco (no solo filas vacías)
    if len(fotos_anexo) < MIN_FOTOS_CIERRE:
        msg = (
            f"El informe PDF exige al menos {MIN_FOTOS_CIERRE} fotografías legibles en disco. "
            f"Solo se encontraron {len(fotos_anexo)} archivo(s). "
            f"Revise «Fotos de evidencia» y vuelva a cargar."
        )
        if getattr(request.user, "is_staff", False):
            messages.error(request, msg)
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
            )
        return HttpResponse(msg, status=400, content_type="text/plain; charset=utf-8")
    croquis_img, croquis_pdf_paths = _croquis_anexo_para_pdf(caso)
    informes_pdf_paths, informes_pdf_meta = _informes_pdf_adjuntos_para_fusion(caso)
    html = render_to_string(
        "inspecciones/caso_rojo_informe_pdf.html",
        {
            "caso": caso,
            "nombre_display": nombre,
            "sections": build_report_sections(caso),
            "fotos_anexo": fotos_anexo,
            "croquis_anexo": croquis_img,
            "croquis_pdf_count": len(croquis_pdf_paths),
            "informes_pdf_anexo": informes_pdf_meta,
            "informes_pdf_count": len(informes_pdf_paths),
            "generado": timezone.localtime(timezone.now()),
        },
        request=request,
    )
    pdf_bytes = _html_to_pdf(
        html, request.build_absolute_uri("/"), f"informe-rojo-{caso.hab_id}.pdf"
    )
    # Orden de fusión: croquis PDF → informes PDF propios (campo / formato libre)
    anexos_fusion = list(croquis_pdf_paths) + list(informes_pdf_paths)
    if anexos_fusion:
        pdf_bytes = _fusionar_pdfs_anexo(pdf_bytes, anexos_fusion)
    filename = f"informe-rojo-{caso.hab_id}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def _fotos_anexo_para_pdf(caso: CasoRojo) -> list[dict]:
    """Rutas file:// a evidencias en disco (WeasyPrint no depende de HTTP/media)."""
    from pathlib import Path

    anexo: list[dict] = []
    for foto in caso.fotos.order_by("created_at", "pk"):
        if not foto.imagen:
            continue
        try:
            path = Path(foto.imagen.path)
        except (ValueError, OSError):
            continue
        if not path.is_file():
            continue
        anexo.append(
            {
                "src": path.resolve().as_uri(),
                "descripcion": (foto.descripcion or "").strip(),
                "fecha": foto.created_at,
            }
        )
    return anexo


_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _croquis_anexo_para_pdf(caso: CasoRojo) -> tuple[list[dict], list]:
    """
    Croquis imagen → anexo HTML (una hoja).
    Croquis PDF → lista de paths para fusionar al PDF final (páginas completas).
    """
    from pathlib import Path

    imagenes: list[dict] = []
    pdfs: list = []
    for croq in caso.croquis.order_by("created_at", "pk"):
        if not croq.archivo:
            continue
        try:
            path = Path(croq.archivo.path)
        except (ValueError, OSError):
            continue
        if not path.is_file():
            continue
        titulo = (croq.titulo or croq.nombre_archivo_origen or "").strip()
        notas = (croq.notas or "").strip()
        desc = " — ".join(p for p in (titulo, notas) if p)
        ext = path.suffix.lower()
        if ext == ".pdf":
            pdfs.append(path.resolve())
            continue
        if ext and ext not in _IMG_EXT:
            continue
        imagenes.append(
            {
                "src": path.resolve().as_uri(),
                "descripcion": desc,
                "fecha": croq.created_at,
                "nombre": path.name,
            }
        )
    return imagenes, pdfs


def _informes_pdf_adjuntos_para_fusion(caso: CasoRojo) -> tuple[list, list[dict]]:
    """PDF propios (formato libre) adjuntos al caso → fusión al final del informe."""
    from pathlib import Path

    paths: list = []
    meta: list[dict] = []
    for doc in caso.informes_pdf.order_by("created_at", "pk"):
        if not doc.archivo:
            continue
        try:
            path = Path(doc.archivo.path)
        except (ValueError, OSError):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        paths.append(path.resolve())
        titulo = (doc.titulo or doc.nombre_archivo_origen or path.name).strip()
        meta.append(
            {
                "titulo": titulo,
                "tipo": (doc.tipo_informe or "").strip(),
                "codigo": (doc.codigo_documento or "").strip(),
                "fecha": doc.created_at,
                "nombre": path.name,
            }
        )
    return paths, meta


def _fusionar_pdfs_anexo(pdf_principal: bytes, anexos_pdf: list) -> bytes:
    """Concatena PDF adjuntos al informe generado (calidad original)."""
    from io import BytesIO

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return pdf_principal

    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(pdf_principal)))
    for path in anexos_pdf:
        try:
            writer.append(str(path))
        except Exception:
            continue
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


@staff_member_required
@require_GET
def guia_usuario_pdf(request) -> HttpResponse:
    """Guía didáctica de usuario (PDF). Borrador hasta aprobación explícita."""
    borrador = not getattr(settings, "GUIA_USUARIO_PDF_APROBADA", False)
    pdf = render_guia_usuario_pdf(request=request, borrador=borrador)
    suffix = "borrador" if borrador else "aprobada"
    filename = f"guia-usuario-fase2-rojo-{suffix}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@staff_member_required
def ver_informe_pdf_adjunto(request, pk: int) -> FileResponse:
    """Sirve el PDF original adjunto (formato libre)."""
    doc = get_object_or_404(InformePdfAdjunto, pk=pk)
    if not usuario_puede_ver_caso(request.user, doc.caso):
        return HttpResponse(status=403)
    filename = doc.nombre_archivo_origen or f"informe-{doc.caso.hab_id}.pdf"
    response = FileResponse(doc.archivo.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def _filtrar_queryset_mapa(request, qs):
    from inspecciones.operacion_stats import _q_sin_dictamen

    # Por defecto: solo bandeja de equipos (no el inventario completo de pendientes).
    universo = (request.GET.get("universo") or "bandeja").strip().lower()
    if universo not in ("todos", "inventario", "all"):
        qs = qs_bandeja_equipos(qs)

    estado = request.GET.get("estado")
    decision = request.GET.get("decision")
    banda = request.GET.get("banda")
    min_score = request.GET.get("min_score")
    if estado:
        qs = qs.filter(estado_2da=estado)
    if decision:
        if decision.lower() in ("sin", "pendiente", "none"):
            qs = qs.filter(_q_sin_dictamen())
        else:
            qs = qs.filter(decision_D__istartswith=decision.upper())
    if banda:
        qs = qs.filter(banda=banda)
    if min_score:
        try:
            qs = qs.filter(score__gte=int(min_score))
        except ValueError:
            pass
    return qs


@staff_member_required
@require_GET
def casos_geojson(request):
    """GeoJSON de casos con coordenadas para el mapa (solo alcance del rol)."""
    qs = _filtrar_queryset_mapa(request, filtrar_casos_por_rol(request.user))

    # Si hay foco a un caso concreto, asegurar que entre aunque no esté en bandeja.
    caso_foco = (request.GET.get("caso") or "").strip()
    if caso_foco:
        try:
            hab = int(caso_foco)
            extra = filtrar_casos_por_rol(request.user).filter(hab_id=hab)
            qs = (qs | extra).distinct()
        except ValueError:
            pass

    features = []
    for c in filtrar_casos_con_gps(qs.iterator()):
        coords = coordenadas_caso(c)
        if not coords:
            continue
        lat, lng = coords
        nombre = c.nombre_conf or c.nombre_hab or f"ID {c.hab_id}"
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
                "properties": {
                    "hab_id": c.hab_id,
                    "nombre": nombre,
                    "score": c.score,
                    "banda": c.banda,
                    "estado": c.estado_2da,
                    "decision": c.decision_D,
                    "prioridad": c.prioridad,
                    "direccion": c.direccion_hab,
                    "muni_parr": c.muni_parr,
                    "admin_url": f"/admin/inspecciones/casorojo/{c.pk}/change/",
                },
            }
        )
    return JsonResponse({"type": "FeatureCollection", "features": features})


@staff_member_required
@require_GET
def geologia_leyenda(request):
    """
    Proxy leyenda Macrostrat carto para el bbox del mapa.
    Evita CORS y permite listar unidades/colores visibles en la vista.
    """
    bounds = (request.GET.get("bounds") or "").strip()
    zoom = (request.GET.get("zoom") or "11").strip()
    parts = [p.strip() for p in bounds.split(",")]
    if len(parts) != 4:
        return JsonResponse(
            {"ok": False, "error": "bounds=oeste,sur,este,norte"}, status=400
        )
    try:
        nums = [float(p) for p in parts]
        z = int(float(zoom))
    except ValueError:
        return JsonResponse({"ok": False, "error": "bounds/zoom inválidos"}, status=400)
    z = max(0, min(z, 14))
    # Sanidad geográfica (Caracas / costa VE)
    w, s, e, n = nums
    if not (-80 <= w < e <= -50 and 0 <= s < n <= 20):
        return JsonResponse({"ok": False, "error": "bbox fuera de rango"}, status=400)
    qs = urlencode({"bounds": f"{w},{s},{e},{n}", "zoom": str(z)})
    url = f"https://dev.macrostrat.org/api/v3/map/carto/legend?{qs}"
    try:
        req = Request(url, headers={"User-Agent": "CPEH-Fase2-ROJO/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=12) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except (URLError, HTTPError, TimeoutError, ValueError, OSError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)[:200]}, status=502)

    units = []
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("success", data).get("data", data.get("data", []))
        if not isinstance(rows, list):
            rows = []
    else:
        rows = []

    def _fmt_edad_ma(t_age, b_age, age_txt: str) -> str:
        """Edad legible: intervalo Macrostrat + Ma (millones de años)."""
        parts: list[str] = []
        if age_txt:
            parts.append(age_txt)
        try:
            t = float(t_age) if t_age is not None else None
            b = float(b_age) if b_age is not None else None
        except (TypeError, ValueError):
            t, b = None, None
        if t is not None and b is not None:
            if abs(t - b) < 1e-9:
                parts.append(f"{t:g} Ma")
            else:
                # Macrostrat: t_age = tope (más joven), b_age = base (más antigua)
                young, old = (t, b) if t <= b else (b, t)
                parts.append(f"{young:g}–{old:g} Ma")
        elif t is not None:
            parts.append(f"≈{t:g} Ma")
        elif b is not None:
            parts.append(f"≈{b:g} Ma")
        # Dedup manteniendo orden
        seen: set[str] = set()
        out: list[str] = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return " · ".join(out)

    def _impacto_hint(age_txt: str, lith: str, t_age, b_age) -> str:
        """
        Orientación contextual para el estudio post-sismo (no es dictamen geotécnico).
        """
        blob = f"{age_txt} {lith}".lower()
        try:
            young = float(t_age) if t_age is not None else None
        except (TypeError, ValueError):
            young = None
        # Sedimentos recientes / cuaternario
        if any(
            k in blob
            for k in (
                "holocene",
                "pleistocene",
                "quaternary",
                "alluv",
                "colluv",
                "sand",
                "gravel",
                "silt",
                "clay",
                "fill",
            )
        ) or (young is not None and young < 2.6):
            return (
                "Unidad joven / depósitos sueltos: suele asociarse a mayor amplificación "
                "sísmica y asientos; contrastar con daños de visita 2 (preexistentes vs sismo)."
            )
        if any(
            k in blob
            for k in (
                "neogene",
                "miocene",
                "pliocene",
                "paleogene",
                "tertiary",
            )
        ) or (young is not None and young < 66):
            return (
                "Roca/formación relativamente joven: respuesta intermedia; "
                "revisar pendientes, rellenos y daños locales en la ficha."
            )
        if any(
            k in blob
            for k in (
                "granite",
                "gneiss",
                "schist",
                "metamorphic",
                "intrusive",
                "basalt",
                "cretaceous",
                "jurassic",
                "ordovician",
                "paleozoic",
                "proterozoic",
            )
        ):
            return (
                "Roca más antigua / competente en mapa: menor amplificación típica en suelo "
                "blando, pero fallas, escarpes y daños estructurales siguen mandando en campo."
            )
        return (
            "Use la edad/litología como contexto del sitio; el daño observado y la decisión D "
            "de Fase II prevalecen sobre esta capa."
        )

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = (row.get("map_unit_name") or row.get("strat_name") or "").strip()
        color = (row.get("color") or "").strip()
        if not name or name.lower() in ("water", "unmapped"):
            continue
        if not color or color.lower() in ("null", "none"):
            continue
        age_txt = (row.get("age") or "").strip()
        lith = (row.get("lith") or "").strip()
        t_age = row.get("t_age")
        b_age = row.get("b_age")
        units.append(
            {
                "nombre": name,
                "edad": age_txt,
                "edad_detalle": _fmt_edad_ma(t_age, b_age, age_txt),
                "t_age": t_age,
                "b_age": b_age,
                "litologia": lith,
                "impacto": _impacto_hint(age_txt, lith, t_age, b_age),
                "color": color if color.startswith("#") else f"#{color}",
                "area": row.get("area"),
            }
        )
    # Más área primero (lo más visible en la vista)
    units.sort(key=lambda u: float(u["area"] or 0), reverse=True)
    return JsonResponse(
        {
            "ok": True,
            "units": units[:40],
            "n": len(units),
            "nota_estudio": (
                "Antigüedad = edad geológica de la unidad (millones de años, Ma). "
                "Sirve de contexto para el estudio de daños post-sismo 24-jun-2026; "
                "no sustituye inspección, geotécnica ni el dictamen D de Fase II."
            ),
        }
    )


@staff_member_required
def mapa_casos(request):
    """Mapa operativo de casos ROJO con GPS (alcance por rol)."""
    base = filtrar_casos_por_rol(request.user)
    bandeja = qs_bandeja_equipos(base)
    estados = (
        bandeja.exclude(estado_2da="")
        .values_list("estado_2da", flat=True)
        .distinct()
        .order_by("estado_2da")
    )
    bandas = (
        bandeja.exclude(banda="")
        .values_list("banda", flat=True)
        .distinct()
        .order_by("banda")
    )
    total_bandeja = len(filtrar_casos_con_gps(bandeja.iterator()))
    total_inventario = len(filtrar_casos_con_gps(base.iterator()))
    caso_foco = request.GET.get("caso")
    universo = (request.GET.get("universo") or "bandeja").strip().lower()
    if universo in ("todos", "inventario", "all"):
        universo = "todos"
    else:
        universo = "bandeja"
    flujo = FlujoRevision()
    return render(
        request,
        "inspecciones/mapa_casos.html",
        {
            "estados": estados,
            "bandas": bandas,
            "total_mapa": total_bandeja if universo == "bandeja" else total_inventario,
            "total_bandeja": total_bandeja,
            "total_inventario": total_inventario,
            "universo": universo,
            "caso_foco": caso_foco,
            "flujo_pasos": flujo.pasos,
        },
    )

