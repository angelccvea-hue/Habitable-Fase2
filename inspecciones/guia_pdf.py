"""Generación PDF — Guía de usuario Fase II ROJO."""
from __future__ import annotations

from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from inspecciones.models import CasoRojo, PartidaCatalogo
from inspecciones.partidas_catalogo import asegurar_partidas_catalogo
from inspecciones.report_sections import build_report_sections


def _caso_ejemplo() -> CasoRojo | None:
    """Caso real del sistema para el anexo (preferir Franco Mar / con dictamen)."""
    caso = (
        CasoRojo.objects.filter(Q(nombre_hab__icontains="Franco") | Q(nombre_conf__icontains="Franco"))
        .order_by("-score")
        .first()
    )
    if caso:
        return caso
    caso = (
        CasoRojo.objects.exclude(decision_D__in=["", "Pendiente"])
        .exclude(decision_D__isnull=True)
        .order_by("-score", "-updated_at")
        .first()
    )
    if caso:
        return caso
    return CasoRojo.objects.order_by("-score").first()


def _ejemplos_llenado() -> list[dict]:
    """Ejemplos didácticos de metrados (cantidades ilustrativas)."""
    return [
        {
            "titulo": "Ejemplo 1 — Reparación local (D2 / M1)",
            "perfil": "Edificio habitado parcialmente; daño concentrado en 2–3 columnas de PB",
            "decision": "D2 — Reparar / reconstruir",
            "magnitud": "M1 — Reparación local",
            "narrativa": (
                "Visita 2 confirma ROJO por columnas de planta baja con daño severo localizado. "
                "El resto del edificio presenta fisuras menores en mampostería. "
                "Camino esperado: apuntalar, reparar/reforzar elementos puntuales y proteger fachada."
            ),
            "totales": {
                "Área aprox. (m²)": "2 400",
                "N.º viviendas": "48",
                "Niveles a intervenir": "PB + piso 1",
                "% estructura a intervenir": "<10%",
                "Confianza global": "Alta",
                "Notas": "Conteo de columnas en PB verificado en sitio; área por planta estimada.",
            },
            "lineas": [
                {"orden": 1, "codigo": "ACORD_PERIM", "elemento": "Entorno / vía", "ubicacion": "Frente calle", "cantidad": "40", "unidad": "m", "severidad": "B", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 2, "codigo": "APUNT_COL", "elemento": "Columna", "ubicacion": "PB ejes B-2, B-3, C-2", "cantidad": "3", "unidad": "und", "severidad": "C", "accion": "Apuntalar / shoring", "confianza": "Alta"},
                {"orden": 3, "codigo": "REP_COL_LOCAL", "elemento": "Columna", "ubicacion": "PB mismos ejes", "cantidad": "3", "unidad": "und", "severidad": "C", "accion": "Reparar", "confianza": "Alta"},
                {"orden": 4, "codigo": "INY_FISURA", "elemento": "Muro / pantalla", "ubicacion": "PB–1 pasillo", "cantidad": "25", "unidad": "m", "severidad": "A", "accion": "Reparar", "confianza": "Media"},
                {"orden": 5, "codigo": "FAC_MAMPOST", "elemento": "Fachada", "ubicacion": "Calle, tramo PB", "cantidad": "18", "unidad": "m²", "severidad": "B", "accion": "Retirar / desmontar", "confianza": "Media"},
            ],
            "nota_cierre": "Decisión D2/M1. Resumen ejecutivo: daño localizado; intervención acotada; sin demolición.",
        },
        {
            "titulo": "Ejemplo 2 — Reparación importante / refuerzo (D2 / M2–M3)",
            "perfil": "Torre 10–12 pisos; piso crítico intermedio; >30% columnas afectadas en ese nivel",
            "decision": "D2 — Reparar / reconstruir",
            "magnitud": "M2 o M3 según alcance del refuerzo",
            "narrativa": (
                "Piso crítico con pérdida de capacidad en varias columnas y vigas. "
                "Se requiere apuntalamiento por niveles, refuerzo (encamisado/perfiles) y "
                "posible reconstrucción parcial de losa. Demoler no es la línea del programa."
            ),
            "totales": {
                "Área aprox. (m²)": "6 800",
                "N.º viviendas": "96",
                "Niveles a intervenir": "Pisos 4–6 (+ apuntalar 3–7)",
                "% estructura a intervenir": "10–30% o >30% (según conteo)",
                "Confianza global": "Media",
                "Notas": "% de columnas por muestreo de ejes; área por planta × N pisos.",
            },
            "lineas": [
                {"orden": 1, "codigo": "ACORD_PERIM", "elemento": "Entorno / vía", "ubicacion": "Perímetro", "cantidad": "120", "unidad": "m", "severidad": "B", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 2, "codigo": "PROT_PEAT", "elemento": "Fachada", "ubicacion": "Calle principal", "cantidad": "60", "unidad": "m", "severidad": "B", "accion": "Acordonar / proteger", "confianza": "Media"},
                {"orden": 3, "codigo": "APUNT_PISO", "elemento": "Edificio completo", "ubicacion": "Pisos 3–7", "cantidad": "5", "unidad": "piso", "severidad": "C", "accion": "Apuntalar / shoring", "confianza": "Media"},
                {"orden": 4, "codigo": "REF_COL", "elemento": "Columna", "ubicacion": "Piso 5 ejes A–D", "cantidad": "12", "unidad": "und", "severidad": "C", "accion": "Reforzar", "confianza": "Media"},
                {"orden": 5, "codigo": "REF_VIGA", "elemento": "Viga", "ubicacion": "Piso 5", "cantidad": "8", "unidad": "und", "severidad": "B", "accion": "Reforzar", "confianza": "Media"},
                {"orden": 6, "codigo": "REP_LOSA", "elemento": "Losa", "ubicacion": "Piso 5 zona central", "cantidad": "90", "unidad": "m²", "severidad": "B", "accion": "Reparar", "confianza": "Estimada"},
                {"orden": 7, "codigo": "FAC_VIDRIO", "elemento": "Fachada", "ubicacion": "Pisos 4–6", "cantidad": "40", "unidad": "und", "severidad": "B", "accion": "Retirar / desmontar", "confianza": "Estimada"},
                {"orden": 8, "codigo": "MOV_EQUIPO", "elemento": "Edificio completo", "ubicacion": "Obra", "cantidad": "1", "unidad": "glb", "severidad": "Pendiente", "accion": "Otro", "confianza": "Estimada"},
            ],
            "nota_cierre": "D2 con M2/M3. Prioridad Alta. Metrados alimentan anteproyecto de reparación, no demolición.",
        },
        {
            "titulo": "Ejemplo 3 — Complementos primero (D1)",
            "perfil": "Daño grave sospechado pero sin acceso suficiente a elementos estructurales",
            "decision": "D1 — Complementos requeridos",
            "magnitud": "N/A (no es D2)",
            "narrativa": (
                "No se puede cerrar aún en reparar: falta evidencia (elementos ocultos, suelo, ensayos). "
                "La Fase II sí cierra con plan D1: códigos GEO/ENS/INV, plazo y medidas inmediatas. "
                "Los metrados de obra definitiva se completan tras los estudios."
            ),
            "totales": {
                "Área aprox. (m²)": "3 100 (estimada)",
                "N.º viviendas": "36",
                "Niveles a intervenir": "Por definir tras ensayos",
                "% estructura a intervenir": "No observable",
                "Confianza global": "Estimada",
                "Notas": "Acceso <50% a miembros; no forzar D2 sin evidencia.",
            },
            "lineas": [
                {"orden": 1, "codigo": "ACORD_PERIM", "elemento": "Entorno / vía", "ubicacion": "Perímetro", "cantidad": "80", "unidad": "m", "severidad": "B", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 2, "codigo": "APUNT_COL", "elemento": "Columna", "ubicacion": "PB zona accesible", "cantidad": "4", "unidad": "und", "severidad": "C", "accion": "Apuntalar / shoring", "confianza": "Media"},
                {"orden": 3, "codigo": "EST_GEO", "elemento": "Cimentación", "ubicacion": "Lote", "cantidad": "1", "unidad": "glb", "severidad": "Pendiente", "accion": "Estudio / ensayo", "confianza": "Alta"},
                {"orden": 4, "codigo": "EST_ENS", "elemento": "Columna", "ubicacion": "PB–piso 2", "cantidad": "6", "unidad": "und", "severidad": "Pendiente", "accion": "Estudio / ensayo", "confianza": "Alta"},
                {"orden": 5, "codigo": "EST_INV", "elemento": "Edificio completo", "ubicacion": "Núcleo", "cantidad": "1", "unidad": "glb", "severidad": "Pendiente", "accion": "Estudio / ensayo", "confianza": "Alta"},
                {"orden": 6, "codigo": "EST_REI", "elemento": "Edificio completo", "ubicacion": "—", "cantidad": "1", "unidad": "und", "severidad": "Pendiente", "accion": "Monitorear", "confianza": "Alta"},
                {"orden": 7, "codigo": "MOV_VIGILANCIA", "elemento": "Entorno / vía", "ubicacion": "Custodia", "cantidad": "30", "unidad": "und", "severidad": "Pendiente", "accion": "Otro", "confianza": "Estimada"},
            ],
            "nota_cierre": "En Decisión: complementos GEO,ENS,INV,REI + plazo + medidas. No marcar D2 hasta tener resultados.",
        },
        {
            "titulo": "Ejemplo 4 — Última instancia demolición (D3) — excepcional",
            "perfil": "Colapso progresivo evidente / pérdida de verticalidad incompatible con reparación",
            "decision": "D3 — Demoler (solo si es inevitable)",
            "magnitud": "N/A",
            "narrativa": (
                "No es el caso típico del programa. Solo si la visita demuestra que reparar "
                "no es viable con seguridad. Exige justificación reforzada, evidencia fotográfica "
                "contundente y revisión/escalamiento. No use este perfil «por defecto»."
            ),
            "totales": {
                "Área aprox. (m²)": "1 800",
                "Vol. escombros estimado (m³)": "2 200 (estimado)",
                "N.º viviendas": "24 (reubicación)",
                "% estructura a intervenir": ">50%",
                "Confianza global": "Alta",
                "Notas": "Documentar por qué se descartó D2; adjuntar fotos de colapso/inclinación.",
            },
            "lineas": [
                {"orden": 1, "codigo": "ACORD_PERIM", "elemento": "Entorno / vía", "ubicacion": "Perímetro ampliado", "cantidad": "150", "unidad": "m", "severidad": "C", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 2, "codigo": "PROT_PEAT", "elemento": "Entorno / vía", "ubicacion": "Aceras", "cantidad": "80", "unidad": "m", "severidad": "C", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 3, "codigo": "DEM_TOTAL", "elemento": "Edificio completo", "ubicacion": "Lote", "cantidad": "1", "unidad": "glb", "severidad": "C", "accion": "Demoler", "confianza": "Alta"},
                {"orden": 4, "codigo": "ESC_RETIRO", "elemento": "Edificio completo", "ubicacion": "Lote", "cantidad": "2200", "unidad": "m³", "severidad": "C", "accion": "Retirar / desmontar", "confianza": "Estimada"},
                {"orden": 5, "codigo": "ESC_TRANSP", "elemento": "Entorno / vía", "ubicacion": "Disposición", "cantidad": "2200", "unidad": "m³", "severidad": "Pendiente", "accion": "Retirar / desmontar", "confianza": "Estimada"},
                {"orden": 6, "codigo": "ESC_LIMPIEZA", "elemento": "Edificio completo", "ubicacion": "Lote", "cantidad": "600", "unidad": "m²", "severidad": "Pendiente", "accion": "Otro", "confianza": "Estimada"},
                {"orden": 7, "codigo": "EST_ALE", "elemento": "Entorno / vía", "ubicacion": "Aledaños", "cantidad": "1", "unidad": "glb", "severidad": "B", "accion": "Estudio / ensayo", "confianza": "Alta"},
            ],
            "nota_cierre": "Excepción. El revisor debe validar que no había vía de reparación razonable.",
        },
        {
            "titulo": "Ejemplo 5 — Ya colapsado / escombros (D4) — excepcional",
            "perfil": "Edificio colapsado total o parcial; lote con escombros; no hay estructura recuperable",
            "decision": "D4 — Escombros / ya colapsado",
            "magnitud": "N/A",
            "narrativa": (
                "No hay edificio que reparar: el trabajo es seguridad perimetral, retiro y disposición. "
                "Sigue siendo excepcional respecto al universo ROJO reparable. "
                "Documente ocupación previa, riesgo a aledaños y volumen estimado."
            ),
            "totales": {
                "Área aprox. del lote (m²)": "900",
                "Vol. escombros estimado (m³)": "1 500",
                "N.º viviendas": "18 (ya desalojadas / reubicadas)",
                "% estructura a intervenir": ">50% (colapsada)",
                "Confianza global": "Media",
                "Notas": "Volumen por área de planta × altura colapsada aproximada.",
            },
            "lineas": [
                {"orden": 1, "codigo": "ACORD_PERIM", "elemento": "Entorno / vía", "ubicacion": "Perímetro", "cantidad": "100", "unidad": "m", "severidad": "C", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 2, "codigo": "PROT_PEAT", "elemento": "Entorno / vía", "ubicacion": "Aceras", "cantidad": "50", "unidad": "m", "severidad": "B", "accion": "Acordonar / proteger", "confianza": "Alta"},
                {"orden": 3, "codigo": "DEM_TOTAL", "elemento": "Edificio completo", "ubicacion": "Restos", "cantidad": "1", "unidad": "glb", "severidad": "C", "accion": "Demoler", "confianza": "Media"},
                {"orden": 4, "codigo": "ESC_RETIRO", "elemento": "Edificio completo", "ubicacion": "Lote", "cantidad": "1500", "unidad": "m³", "severidad": "C", "accion": "Retirar / desmontar", "confianza": "Estimada"},
                {"orden": 5, "codigo": "ESC_TRANSP", "elemento": "Entorno / vía", "ubicacion": "Disposición", "cantidad": "1500", "unidad": "m³", "severidad": "Pendiente", "accion": "Retirar / desmontar", "confianza": "Estimada"},
                {"orden": 6, "codigo": "ESC_LIMPIEZA", "elemento": "Edificio completo", "ubicacion": "Lote", "cantidad": "900", "unidad": "m²", "severidad": "Pendiente", "accion": "Otro", "confianza": "Estimada"},
                {"orden": 7, "codigo": "MOV_VIGILANCIA", "elemento": "Entorno / vía", "ubicacion": "Custodia", "cantidad": "15", "unidad": "und", "severidad": "B", "accion": "Otro", "confianza": "Estimada"},
            ],
            "nota_cierre": "D4 + prioridad según riesgo vial. No forzar metrados de reparación.",
        },
    ]


def render_guia_usuario_pdf(*, request=None, borrador: bool = True) -> bytes:
    """Renderiza la guía didáctica a bytes PDF (incluye anexo de informe ejemplo)."""
    asegurar_partidas_catalogo()
    ejemplo = _caso_ejemplo()
    partidas = list(
        PartidaCatalogo.objects.filter(activo=True).order_by("orden", "grupo", "codigo")
    )
    ctx = {
        "generado": timezone.localtime(timezone.now()),
        "borrador": borrador,
        "version_guia": "1.4.0-borrador" if borrador else "1.4.0",
        "ejemplo_caso": ejemplo,
        "ejemplo_nombre": "",
        "ejemplo_sections": [],
        "ejemplo_hab_id": "",
        "ejemplo_decision": "",
        "ejemplo_estado": "",
        "ejemplo_score": "",
        "partidas": partidas,
        "ejemplos_llenado": _ejemplos_llenado(),
    }
    if ejemplo:
        ctx["ejemplo_nombre"] = ejemplo.nombre_conf or ejemplo.nombre_hab or f"ID {ejemplo.hab_id}"
        ctx["ejemplo_sections"] = build_report_sections(ejemplo)
        ctx["ejemplo_hab_id"] = ejemplo.hab_id
        ctx["ejemplo_decision"] = ejemplo.decision_D or "Pendiente"
        ctx["ejemplo_estado"] = ejemplo.estado_2da or "—"
        ctx["ejemplo_score"] = ejemplo.score if ejemplo.score is not None else "—"

    if request is not None:
        html = render_to_string("inspecciones/guia_usuario_pdf.html", ctx, request=request)
        base_url = request.build_absolute_uri("/")
    else:
        html = render_to_string("inspecciones/guia_usuario_pdf.html", ctx)
        base_url = "http://127.0.0.1/"
    try:
        from weasyprint import HTML

        return HTML(string=html, base_url=base_url).write_pdf()
    except Exception:
        from inspecciones.operacion_views import _pdf_via_edge

        return _pdf_via_edge(html, "guia-usuario.pdf")
