from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.views.static import serve

from inspecciones.asignacion_lote_views import asignacion_lote_excel, plantilla_asignacion_lote
from inspecciones.asignacion_views import tablero_asignacion
from inspecciones.export_views import (
    export_excel_informe,
    export_excel_informes_multiples,
    export_excel_lote,
)
from inspecciones.import_views import cargar_excel_informe, ver_croquis_adjunto
from inspecciones.operacion_views import (
    export_operacion_excel,
    export_operacion_pdf,
    tablero_operacion,
)
from inspecciones.procedimientos_pdf_views import (
    ficha_procedimiento_dxf,
    ficha_procedimiento_pdf,
)
from inspecciones.plano_metrado_views import (
    visor_plano_metrado,
    visor_plano_metrado_guardar,
)
from inspecciones.perfil_views import gestionar_nombres_usuarios, mi_perfil
from inspecciones.usuarios_views import gestion_usuarios
from inspecciones.views import (
    casos_geojson,
    geologia_leyenda,
    guia_usuario_pdf,
    health,
    mapa_casos,
    ver_informe_pdf_adjunto,
)

admin.site.site_header = "CPEH — Habitable Fase II"
admin.site.site_title = "CPEH Fase II"
admin.site.index_title = "Panel de administración"

urlpatterns = [
    path("", lambda request: redirect("admin:index")),
    path("api/health/", health),
    path("api/casos/geojson/", casos_geojson, name="casos_geojson"),
    path("api/geologia/leyenda/", geologia_leyenda, name="geologia_leyenda"),
    path("informes/pdf/<int:pk>/", ver_informe_pdf_adjunto, name="ver_informe_pdf_adjunto"),
    path("croquis/<int:pk>/", ver_croquis_adjunto, name="ver_croquis_adjunto"),
    path("guia/usuario.pdf", guia_usuario_pdf, name="guia_usuario_pdf"),
    path(
        "catalogo/procedimientos/<str:codigo>.pdf",
        ficha_procedimiento_pdf,
        name="ficha_procedimiento_pdf",
    ),
    path(
        "catalogo/procedimientos/<str:codigo>.dxf",
        ficha_procedimiento_dxf,
        name="ficha_procedimiento_dxf",
    ),
    path("mapa/", mapa_casos, name="mapa_casos"),
    path("asignacion/", tablero_asignacion, name="tablero_asignacion"),
    path("asignacion/lote/", asignacion_lote_excel, name="asignacion_lote_excel"),
    path(
        "asignacion/lote/plantilla.xlsx",
        plantilla_asignacion_lote,
        name="plantilla_asignacion_lote",
    ),
    path("perfil/", mi_perfil, name="mi_perfil"),
    path("perfil/equipo/", gestionar_nombres_usuarios, name="gestionar_nombres"),
    path("gestion/usuarios/", gestion_usuarios, name="gestion_usuarios"),
    path("operacion/", tablero_operacion, name="tablero_operacion"),
    path("operacion/export.xlsx", export_operacion_excel, name="export_operacion_excel"),
    path("operacion/export.pdf", export_operacion_pdf, name="export_operacion_pdf"),
    path("plano-metrado/", visor_plano_metrado, name="visor_plano_metrado"),
    path("plano-metrado/<int:pk>/", visor_plano_metrado, name="visor_plano_metrado_caso"),
    path(
        "plano-metrado/<int:pk>/guardar/",
        visor_plano_metrado_guardar,
        name="visor_plano_metrado_guardar",
    ),
    path("export/excel/informe/<int:pk>/", export_excel_informe, name="export_excel_informe"),
    path("export/excel/lote/", export_excel_lote, name="export_excel_lote"),
    path("export/excel/informes/", export_excel_informes_multiples, name="export_excel_informes_multiples"),
    path("import/excel/", cargar_excel_informe, name="cargar_excel"),
    path("import/excel/caso/<int:pk>/", cargar_excel_informe, name="cargar_excel_caso"),
    path("admin/", admin.site.urls),
    # Media siempre vía app (Apache hace proxy total a Gunicorn; sin esto falla con DEBUG=0).
    path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
]
