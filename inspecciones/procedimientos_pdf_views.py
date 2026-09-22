"""Vista PDF de fichas del catálogo de procedimientos (+ plantilla CAD PLN-01)."""
from __future__ import annotations

from pathlib import Path

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from inspecciones.fichas_procedimientos import REFERENCIAS_COMUNES, ficha_para
from inspecciones.models import Procedimiento

_PLANTILLA_DXF = (
    Path(__file__).resolve().parent
    / "static"
    / "plantillas"
    / "PLN-01-plano-inspeccion-ejes.dxf"
)


def _pdf_response(html: str, filename: str) -> HttpResponse:
    try:
        from weasyprint import HTML

        pdf = HTML(string=html, base_url="/").write_pdf()
    except Exception:
        from inspecciones.operacion_views import _pdf_via_edge

        pdf = _pdf_via_edge(html, filename)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


@staff_member_required
def ficha_procedimiento_pdf(request, codigo: str):
    codigo = (codigo or "").strip().upper()
    ficha = ficha_para(codigo)
    if not ficha:
        proc = get_object_or_404(Procedimiento, codigo__iexact=codigo)
        ficha = {
            "codigo": proc.codigo,
            "categoria": proc.get_categoria_display(),
            "titulo": proc.titulo,
            "alcance": proc.descripcion or "Ficha en elaboración.",
            "aplicar_cuando": ["Consultar lineamientos técnicos vigentes y coordinación."],
            "no_aplicar": [],
            "especificacion": proc.descripcion
            or "Contenido detallado pendiente de carga en el catálogo.",
            "borrador": True,
        }
    html = render_to_string(
        "inspecciones/ficha_procedimiento_pdf.html",
        {
            "ficha": ficha,
            "referencias": REFERENCIAS_COMUNES,
            "generado": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
            "grid_nums": ["7", "6", "5", "4", "3", "2", "1"],
        },
    )
    return _pdf_response(html, f"{ficha['codigo']}.pdf")


@staff_member_required
def ficha_procedimiento_dxf(request, codigo: str):
    """Descarga plantilla CAD (DXF) asociada a la ficha — hoy solo PLN-01."""
    codigo = (codigo or "").strip().upper()
    if codigo != "PLN-01":
        raise Http404("No hay plantilla CAD para este código.")
    if not _PLANTILLA_DXF.is_file():
        raise Http404(
            "Plantilla DXF no generada. Ejecutar inspecciones/plantilla_pln01_dxf.py"
        )
    return FileResponse(
        _PLANTILLA_DXF.open("rb"),
        as_attachment=True,
        filename="PLN-01-plano-inspeccion-ejes.dxf",
        content_type="application/dxf",
    )
