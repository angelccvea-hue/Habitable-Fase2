from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    CasoRojo,
    CredencialEmitida,
    CroquisAdjunto,
    EquipoBrigada,
    EvidenciaFoto,
    HistorialDetallado,
    HistorialEstado,
    InformePdfAdjunto,
    LineaMetrado,
    PartidaCatalogo,
    PlantaInspeccion,
    Procedimiento,
)
from .gps_utils import coordenadas_caso
from .section_labels import CASE_FIELDSETS, get_case_fieldsets_admin
from .forms_admin import CasoRojoAdminForm
from .widgets_admin import CpehClearableFileInput
from .workflow import (
    es_administrador,
    es_coordinador,
    es_revisor,
    es_solo_consulta,
    es_solo_inspector,
    es_solo_revisor,
    filtrar_casos_por_rol,
    opciones_estado_2da,
    puede_asignar_casos,
    puede_modificar_casos,
    puede_transicionar,
    usuario_puede_ver_caso,
    ve_todos_los_casos,
    validar_dictamen,
    validar_transicion_estado,
)


# Tope de filas en el change form: evita POST/HTML gigantes (WORKER TIMEOUT).
# Las filas no mostradas NO se borran al guardar; solo se editan las visibles + altas nuevas.
_INLINE_EDIT_CAP = 40


def _capped_inline_formset(base_formset, *, obj, order_by: tuple[str, ...], cap: int = _INLINE_EDIT_CAP):
    """Formset que solo incluye hasta `cap` filas del caso; el resto no se toca al guardar."""

    class CappedFormSet(base_formset):
        def __init__(self, *args, **kwargs):
            qs = kwargs.get("queryset")
            if (
                qs is not None
                and obj is not None
                and getattr(obj, "pk", None)
            ):
                # El admin pasa el queryset del modelo; filtramos por FK del formset.
                fk_name = self.fk.name
                scoped = qs.filter(**{fk_name: obj.pk}).order_by(*order_by)
                ids = list(scoped.values_list("pk", flat=True)[:cap])
                kwargs["queryset"] = qs.filter(pk__in=ids).order_by(*order_by)
            super().__init__(*args, **kwargs)

    return CappedFormSet


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    fields = ("created_at", "estado_anterior", "estado_nuevo", "usuario", "nota_visible")
    readonly_fields = (
        "estado_anterior",
        "estado_nuevo",
        "usuario",
        "nota_visible",
        "created_at",
    )
    can_delete = True
    show_change_link = False
    verbose_name_plural = (
        "Historial de estados — transición del flujo (admin puede borrar filas)"
    )
    classes = ("cpeh-hist-estados-inline",)

    @admin.display(description="Nota")
    def nota_visible(self, obj: HistorialEstado) -> str:
        nota = (obj.nota or "").strip()
        if nota:
            return nota
        ant = (obj.estado_anterior or "").strip() or "—"
        nuevo = (obj.estado_nuevo or "").strip() or "—"
        return f"Cambio de estado: {ant} → {nuevo}"

    def get_formset(self, request, obj=None, **kwargs):
        BaseFS = super().get_formset(request, obj, **kwargs)
        return _capped_inline_formset(BaseFS, obj=obj, order_by=("-created_at",))

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return es_administrador(request.user)

    def has_delete_permission(self, request, obj=None):
        """Solo superusuario/admin puede eliminar entradas del historial."""
        return es_administrador(request.user)


class HistorialDetalladoInline(admin.TabularInline):
    model = HistorialDetallado
    extra = 0
    fields = ("created_at", "usuario", "resumen", "detalle", "origen")
    readonly_fields = ("created_at", "usuario", "resumen", "detalle", "origen")
    can_delete = True
    show_change_link = False
    classes = ("cpeh-hist-detallado-inline",)
    verbose_name = "Entrada de historial detallado"
    verbose_name_plural = (
        "Historial detallado — qué se hizo y cuándo "
        "(si está vacío: los cambios previos al despliegue se rellenan con el comando "
        "de backfill; los nuevos guardados y cambios de estado sí se registran solos)"
    )

    def get_formset(self, request, obj=None, **kwargs):
        BaseFS = super().get_formset(request, obj, **kwargs)
        return _capped_inline_formset(BaseFS, obj=obj, order_by=("-created_at",))

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)


class LineaMetradoInline(admin.TabularInline):
    model = LineaMetrado
    extra = 5
    max_num = _INLINE_EDIT_CAP + 10
    classes = ("cpeh-metrado-excel-inline",)
    fields = (
        "orden",
        "codigo_partida",
        "partida",
        "elemento",
        "id_pln01",
        "piso_pln",
        "ubicacion",
        "tipo_apuntamiento",
        "cantidad",
        "unidad",
        "severidad",
        "accion",
        "confianza",
        "nota",
    )
    readonly_fields = ()
    autocomplete_fields = ("partida",)
    verbose_name = "Línea de metrado"
    verbose_name_plural = (
        "Líneas de metrado — anclar a PLN-01 (id_pln01) · partida del catálogo · "
        "apuntalamiento preventivo/trabajo. Igual espíritu que Excel «Metrados»."
    )

    class Media:
        css = {"all": ("css/cpeh_admin.css",)}

    def get_formset(self, request, obj=None, **kwargs):
        BaseFS = super().get_formset(request, obj, **kwargs)
        return _capped_inline_formset(BaseFS, obj=obj, order_by=("orden", "id"))

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is None:
            return None
        # Minimalista: sin help bajo cada celda
        formfield.help_text = ""
        if db_field.name == "cantidad":
            formfield.widget.attrs.update(
                {
                    "class": "cpeh-metrado-cantidad",
                    "placeholder": "cant.",
                    "step": "0.001",
                }
            )
        elif db_field.name == "orden":
            formfield.widget.attrs.update({"placeholder": "#"})
        elif db_field.name == "ubicacion":
            formfield.widget.attrs.update({"placeholder": "piso / eje / zona"})
        elif db_field.name == "codigo_partida":
            formfield.widget.attrs.update({"placeholder": "código"})
        elif db_field.name == "nota":
            formfield.widget.attrs.update({"placeholder": "opcional"})
        return formfield


class EvidenciaFotoInline(admin.TabularInline):
    model = EvidenciaFoto
    extra = 0
    max_num = _INLINE_EDIT_CAP + 10
    fields = ("miniatura", "imagen", "descripcion", "fecha")
    readonly_fields = ("miniatura", "fecha")
    verbose_name_plural = (
        f"Evidencias fotográficas (en ficha hasta {_INLINE_EDIT_CAP} más recientes; "
        "el resto permanece y no se borra al guardar)"
    )

    @admin.display(description="Vista")
    def miniatura(self, obj: EvidenciaFoto) -> str:
        if obj and obj.pk and getattr(obj, "imagen", None):
            try:
                url = obj.imagen.url
            except (ValueError, OSError):
                return "—"
            return format_html(
                '<a href="{0}" target="_blank" rel="noopener">'
                '<img src="{0}" class="cpeh-evidencia-thumb" alt="" loading="lazy"></a>',
                url,
            )
        return "—"

    @admin.display(description="Fecha")
    def fecha(self, obj: EvidenciaFoto) -> str:
        if not obj or not obj.pk or not obj.created_at:
            return "—"
        return obj.created_at.strftime("%d/%m/%Y %H:%M")

    def get_formset(self, request, obj=None, **kwargs):
        BaseFS = super().get_formset(request, obj, **kwargs)
        return _capped_inline_formset(BaseFS, obj=obj, order_by=("-created_at",))

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "imagen":
            kwargs["widget"] = CpehClearableFileInput
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is None:
            return formfield
        # Sin help_text en celda: satura el tabular.
        formfield.help_text = ""
        return formfield


class InformePdfAdjuntoInline(admin.TabularInline):
    model = InformePdfAdjunto
    extra = 0
    fields = (
        "titulo",
        "archivo",
        "tipo_informe",
        "codigo_documento",
        "notas",
        "ver_pdf",
        "created_at",
    )
    readonly_fields = ("ver_pdf", "created_at")

    @admin.display(description="Ver")
    def ver_pdf(self, obj: InformePdfAdjunto) -> str:
        if obj.pk and obj.archivo:
            url = reverse("ver_informe_pdf_adjunto", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">Abrir PDF</a>', url
            )
        return "—"


class CroquisAdjuntoInline(admin.TabularInline):
    model = CroquisAdjunto
    extra = 0
    fields = ("codigo_piso", "titulo", "archivo", "notas", "ver_croquis", "created_at")
    readonly_fields = ("ver_croquis", "created_at")

    @admin.display(description="Ver")
    def ver_croquis(self, obj: CroquisAdjunto) -> str:
        if obj.pk and obj.archivo:
            url = reverse("ver_croquis_adjunto", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">Abrir croquis</a>', url
            )
        return "—"


class PlantaInspeccionInline(admin.TabularInline):
    model = PlantaInspeccion
    extra = 2
    fields = ("orden", "codigo_piso", "titulo", "croquis", "activa", "notas")
    autocomplete_fields = ("croquis",)
    verbose_name_plural = (
        "Plantas de inspección (PB, P1…) — selector del visor PLN-01 × MET-01"
    )


@admin.register(CasoRojo)
class CasoRojoAdmin(admin.ModelAdmin):
    form = CasoRojoAdminForm
    change_form_template = "admin/inspecciones/casorojo/change_form.html"
    inlines = [
        PlantaInspeccionInline,
        LineaMetradoInline,
        CroquisAdjuntoInline,
        InformePdfAdjuntoInline,
        EvidenciaFotoInline,
        HistorialEstadoInline,
        HistorialDetalladoInline,
    ]
    list_display = (
        "hab_id",
        "nombre_conf",
        "score",
        "banda",
        "estado_2da",
        "decision_D",
        "prioridad",
        "coordinador_asignado",
        "inspector_asignado",
        "revisor_asignado",
        "fecha_v2",
        "enlace_pdf",
        "enlace_excel",
        "enlace_mapa",
    )
    list_display_links = ("hab_id", "nombre_conf")
    list_filter = (
        "estado_2da",
        "decision_D",
        "prioridad",
        "banda",
        "etiqueta_f1",
        "val_etiqueta",
        "sistema",
        "inspector_asignado",
        "revisor_asignado",
        "coordinador_asignado",
    )
    search_fields = (
        "hab_id",
        "nombre_hab",
        "nombre_conf",
        "certificado",
        "direccion_hab",
        "muni_parr",
        "evaluadores_v2",
    )
    readonly_fields = ("created_at", "updated_at", "lat", "lng")
    # §1 Precarga Habitable: solo lectura salvo administrador (reparar imports).
    # §2 Ranking: siempre fijo en ficha; correcciones solo vía §3 (corr_score / corr_banda)
    # o reimportación del ranking.
    PRECARGA_HABITABLE_READONLY = (
        "hab_id",
        "certificado",
        "nombre_hab",
        "etiqueta_f1",
        "fecha_f1",
        "inspector_f1",
        "direccion_hab",
        "muni_parr",
        "pisos_f1",
        "riesgos_f1",
        "colapso_f1",
        "piso_crit_f1",
        "acciones_f1",
        "obs_f1",
        "gps_hab",
    )
    RANKING_READONLY = (
        "score",
        "banda",
        "puestos",
        "score_detalle",
        "prob_rel",
    )
    PRECARGA_READONLY = PRECARGA_HABITABLE_READONLY + RANKING_READONLY

    autocomplete_fields = ("coordinador_asignado", "inspector_asignado", "revisor_asignado")
    date_hierarchy = "fecha_v2"
    list_per_page = 30
    save_on_top = True
    actions = (
        "descargar_excel_informe",
        "descargar_excel_lote",
        "marcar_en_visita",
        "enviar_a_revision",
        "resetear_datos_prueba",
    )

    @admin.action(
        description="[Admin] Resetear datos de prueba (conserva precarga; borra Excel/PDF/visita)"
    )
    def resetear_datos_prueba(self, request, queryset):
        if not es_administrador(request.user):
            self.message_user(
                request,
                "Solo el administrador (superusuario) puede resetear datos de prueba.",
                level=messages.ERROR,
            )
            return
        n_casos = 0
        for caso in queryset:
            caso.resetear_datos_prueba()
            n_casos += 1
        self.message_user(
            request,
            f"Reset de prueba: {n_casos} caso(s). Precarga intacta; visita/adjuntos/historial limpios.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Descargar Excel informe (1 pestaña/caso)")
    def descargar_excel_informe(self, request, queryset):
        from inspecciones.export_views import respuesta_excel_admin

        resp = respuesta_excel_admin(request, queryset, "informe_multi")
        if resp:
            return resp
        self.message_user(request, "Sin casos seleccionados.", level=messages.WARNING)

    @admin.action(description="Descargar Excel lote (1 fila/caso)")
    def descargar_excel_lote(self, request, queryset):
        from inspecciones.export_views import respuesta_excel_admin

        if queryset.count() > 500:
            self.message_user(request, "Máximo 500 casos por lote.", level=messages.ERROR)
            return
        resp = respuesta_excel_admin(request, queryset, "lote")
        if resp:
            return resp
        self.message_user(request, "Sin casos seleccionados.", level=messages.WARNING)

    @admin.action(description="Marcar seleccionados → En visita")
    def marcar_en_visita(self, request, queryset):
        from inspecciones import choices as ch

        n = 0
        for caso in queryset:
            try:
                validar_transicion_estado(request.user, caso.estado_2da, ch.Estado2daRonda.EN_VISITA)
                anterior = caso.estado_2da
                caso.estado_2da = ch.Estado2daRonda.EN_VISITA
                caso.save(update_fields=["estado_2da", "updated_at"])
                HistorialEstado.objects.create(
                    caso=caso,
                    estado_anterior=anterior,
                    estado_nuevo=caso.estado_2da,
                    usuario=request.user,
                    nota="Acción masiva admin",
                )
                from inspecciones.historial_detalle import registrar_historial_detallado

                registrar_historial_detallado(
                    caso=caso,
                    usuario=request.user,
                    resumen=f"Acción masiva: {anterior} → {caso.estado_2da}",
                    detalle="Marcado En visita desde acción masiva del listado admin.",
                    origen="masivo",
                )
                n += 1
            except ValidationError as exc:
                self.message_user(request, f"{caso.hab_id}: {exc}", level=messages.WARNING)
        self.message_user(request, f"{n} caso(s) marcados En visita.", level=messages.SUCCESS)

    @admin.action(description="Enviar seleccionados → Pendiente revisión")
    def enviar_a_revision(self, request, queryset):
        from inspecciones import choices as ch

        n = 0
        for caso in queryset:
            try:
                validar_transicion_estado(
                    request.user, caso.estado_2da, ch.Estado2daRonda.PENDIENTE_REVISION
                )
                validar_dictamen(caso, cerrar=True)
                anterior = caso.estado_2da
                caso.estado_2da = ch.Estado2daRonda.PENDIENTE_REVISION
                caso.save()
                HistorialEstado.objects.create(
                    caso=caso,
                    estado_anterior=anterior,
                    estado_nuevo=caso.estado_2da,
                    usuario=request.user,
                    nota="Enviado a revisión (acción masiva)",
                )
                from inspecciones.historial_detalle import registrar_historial_detallado

                registrar_historial_detallado(
                    caso=caso,
                    usuario=request.user,
                    resumen=f"Acción masiva: enviado a revisión ({anterior} → {caso.estado_2da})",
                    detalle="Enviado a Pendiente revisión desde acción masiva del listado admin.",
                    origen="masivo",
                )
                n += 1
            except ValidationError as exc:
                self.message_user(request, f"{caso.hab_id}: {exc}", level=messages.WARNING)
        self.message_user(
            request, f"{n} caso(s) enviados a Pendiente revisión.", level=messages.SUCCESS
        )

    @admin.display(description="Excel")
    def enlace_excel(self, obj: CasoRojo) -> str:
        url = reverse("export_excel_informe", args=[obj.pk])
        return format_html('<a href="{}" title="Plantilla informe">XLS</a>', url)

    @admin.display(description="PDF")
    def enlace_pdf(self, obj: CasoRojo) -> str:
        url = reverse("admin:inspecciones_casorojo_pdf", args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">PDF</a>', url)

    @admin.display(description="Mapa")
    def enlace_mapa(self, obj: CasoRojo) -> str:
        if not coordenadas_caso(obj):
            return "—"
        url = reverse("mapa_casos") + f"?caso={obj.hab_id}"
        return format_html('<a href="{}" target="_blank" rel="noopener">Ver</a>', url)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filtrar_casos_por_rol(request.user, qs)

    def changelist_view(self, request, extra_context=None):
        """Revisor: si entra sin filtros, abrir cola «Pendiente revisión» por defecto."""
        from urllib.parse import urlencode

        from django.http import HttpResponseRedirect

        from inspecciones import choices as ch

        if es_solo_revisor(request.user) and request.method == "GET":
            keys = set(request.GET.keys())
            noise = {"o", "ot", "p", "_changelist_filters"}
            if not (keys - noise):
                q = urlencode({"estado_2da__exact": ch.Estado2daRonda.PENDIENTE_REVISION})
                return HttpResponseRedirect(f"{request.path}?{q}")
        extra = extra_context or {}
        if es_solo_revisor(request.user):
            if request.GET.get("estado_2da__exact") == ch.Estado2daRonda.PENDIENTE_REVISION:
                extra.setdefault(
                    "title",
                    "Cola de revisión — Pendiente revisión "
                    "(puede quitar el filtro para ver todos)",
                )
            else:
                extra.setdefault(
                    "title",
                    "Casos ROJO — revisión técnica",
                )
        return super().changelist_view(request, extra_context=extra)

    def has_view_permission(self, request, obj=None):
        if not super().has_view_permission(request, obj):
            return False
        if obj is None:
            return True
        return usuario_puede_ver_caso(request.user, obj)

    def has_change_permission(self, request, obj=None):
        if not puede_modificar_casos(request.user):
            return False
        if not super().has_change_permission(request, obj):
            return False
        if obj is None:
            return True
        return usuario_puede_ver_caso(request.user, obj)

    def has_add_permission(self, request):
        return es_administrador(request.user) and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user) and super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not puede_modificar_casos(request.user):
            return {}
        if not es_administrador(request.user):
            actions.pop("resetear_datos_prueba", None)
        # Lote Excel: admin / coordinador (alcance de bolsa o inventario).
        if not (es_administrador(request.user) or puede_asignar_casos(request.user)):
            actions.pop("descargar_excel_lote", None)
        # Marcar visita / enviar a revisión: también ingenieros (su lista ya está filtrada).
        puede_flujo_campo = (
            es_administrador(request.user)
            or puede_asignar_casos(request.user)
            or es_solo_inspector(request.user)
        )
        if not puede_flujo_campo:
            actions.pop("marcar_en_visita", None)
            actions.pop("enviar_a_revision", None)
        return actions

    def get_list_filter(self, request):
        filters = list(self.list_filter)
        if not es_administrador(request.user) and not ve_todos_los_casos(request.user):
            filters = [
                f
                for f in filters
                if f not in ("inspector_asignado", "revisor_asignado", "coordinador_asignado")
            ]
        return filters

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if es_solo_consulta(request.user):
            return [f.name for f in self.model._meta.fields if f.name not in ("id",)]
        # §2 Ranking: siempre fijo (también admin). §1 precarga: fijo salvo admin.
        ro.extend(self.RANKING_READONLY)
        if not es_administrador(request.user):
            ro.extend(self.PRECARGA_HABITABLE_READONLY)
        asignacion = ["coordinador_asignado", "inspector_asignado", "revisor_asignado"]
        if es_administrador(request.user):
            # Admin tampoco asigna revisor desde ficha (bandeja compartida)
            ro.append("revisor_asignado")
        elif puede_asignar_casos(request.user):
            # Coordinador: no cambia coordinador ni revisor; sí ingeniero
            ro.append("coordinador_asignado")
            ro.append("revisor_asignado")
        else:
            # Revisor e ingeniero: no tocan asignación
            ro.extend(asignacion)
        if es_solo_inspector(request.user) and obj:
            from inspecciones import choices as ch

            if obj.estado_2da in (
                ch.Estado2daRonda.PENDIENTE_REVISION,
                ch.Estado2daRonda.REVISADO,
                ch.Estado2daRonda.APROBADO,
                ch.Estado2daRonda.PUBLICADO,
            ):
                return [f.name for f in self.model._meta.fields if f.name not in ("id",)]
        return list(dict.fromkeys(ro))

    def get_form(self, request, obj=None, change=False, **kwargs):
        """Combo Estado 2da: solo estado actual + siguientes válidos para el rol."""
        Form = super().get_form(request, obj, change=change, **kwargs)
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.forms import ValidationError as FormValidationError

        from inspecciones import choices as ch

        actual = (
            (obj.estado_2da if obj else "") or ch.Estado2daRonda.PENDIENTE
        )
        choices = opciones_estado_2da(request.user, actual)
        n_siguientes = max(0, len(choices) - 1)
        user = request.user
        obj_pk = obj.pk if obj else None

        class FormEstadoFiltrado(Form):
            def __init__(self, *args, **kw):
                super().__init__(*args, **kw)
                campo = self.fields.get("estado_2da")
                if campo is None:
                    return
                campo.choices = choices
                if es_administrador(user):
                    extra = (
                        "Administrador: puede seleccionar y guardar cualquier estado "
                        f"del catálogo (actual: «{actual}»). "
                        f"{len(choices)} opción(es) disponibles."
                    )
                else:
                    pista = {
                        "Pendiente verificación": "barra superior → «Iniciar visita».",
                        "En visita": "barra superior → «Pasar a borrador» (Pend.Rev. aparece después).",
                        "Borrador": "barra superior → «Enviar a revisión».",
                        "Pendiente revisión": "acciones del revisor en la barra / panel Flujo.",
                        "Revisado": "acciones del revisor en la barra / panel Flujo.",
                        "Aprobado": "coordinador: «Publicar caso».",
                    }.get(actual, "vea la barra superior «Flujo».")
                    extra = (
                        f"Estado actual «{actual}»: {n_siguientes} transición(es) en el combo. "
                        f"Recomendado: {pista}"
                    )
                base = (campo.help_text or "").strip()
                campo.help_text = f"{base} {extra}".strip() if base else extra

            def clean(self):
                cleaned = super().clean()
                if self.errors:
                    return cleaned
                if not puede_modificar_casos(user):
                    raise FormValidationError(
                        "Su usuario es solo consulta: no puede modificar casos."
                    )
                if obj_pk and not usuario_puede_ver_caso(user, self.instance):
                    raise FormValidationError("No tiene permiso sobre este caso.")
                nuevo = cleaned.get("estado_2da") or self.instance.estado_2da or ""
                if obj_pk and actual and nuevo and actual != nuevo:
                    try:
                        validar_transicion_estado(user, actual, nuevo)
                    except DjangoValidationError as exc:
                        msgs = getattr(exc, "messages", None) or [str(exc)]
                        raise FormValidationError(list(msgs)) from exc
                return cleaned

        return FormEstadoFiltrado

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Captura ValidationError de save_model → mensaje (no HTTP 500)."""
        from django.http import HttpResponseRedirect

        try:
            return self._change_view_inner(request, object_id, form_url, extra_context)
        except ValidationError as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            for msg in msgs:
                self.message_user(request, msg, level=messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[object_id])
            )

    def _change_view_inner(self, request, object_id, form_url="", extra_context=None):
        from inspecciones import choices as ch
        from inspecciones.workflow import MIN_FOTOS_CIERRE, checklist_cierre

        extra = extra_context or {}
        # Guías wizard: disponibles para cualquier usuario que abra la ficha
        extra["es_admin_reset"] = es_administrador(request.user)
        extra["min_fotos_informe"] = MIN_FOTOS_CIERRE
        extra["n_fotos_adjuntas"] = 0
        extra["checklist_cierre"] = None
        extra["mostrar_guia_wizard"] = True
        extra["show_save_and_add_another"] = False  # no útil en este flujo
        extra["puede_aprobar"] = False
        extra["puede_devolver"] = False
        extra["puede_enviar_revision"] = False
        extra["puede_marcar_revisado"] = False
        extra["puede_publicar"] = False
        extra["puede_iniciar_visita"] = False
        extra["puede_pasar_borrador"] = False
        extra["mostrar_aprobar"] = False
        extra["mostrar_devolver"] = False
        extra["mostrar_enviar_revision"] = False
        extra["mostrar_marcar_revisado"] = False
        extra["mostrar_publicar"] = False
        extra["mostrar_iniciar_visita"] = False
        extra["mostrar_pasar_borrador"] = False
        extra["estado_actual"] = ""
        if object_id:
            try:
                caso = CasoRojo.objects.get(pk=object_id)
                extra["n_fotos_adjuntas"] = caso.fotos.count()
                extra["checklist_cierre"] = checklist_cierre(caso)
                extra["estado_actual"] = caso.estado_2da or ""
                est = caso.estado_2da or ""
                u = request.user
                es_admin = es_administrador(u)
                en_cola = est in (
                    ch.Estado2daRonda.PENDIENTE_REVISION,
                    ch.Estado2daRonda.REVISADO,
                )
                # Botones = estado actual + transición permitida al rol (misma regla que el combo)
                extra["puede_iniciar_visita"] = (
                    est == ch.Estado2daRonda.PENDIENTE
                    and puede_transicionar(u, est, ch.Estado2daRonda.EN_VISITA)
                )
                extra["puede_pasar_borrador"] = (
                    est == ch.Estado2daRonda.EN_VISITA
                    and puede_transicionar(u, est, ch.Estado2daRonda.BORRADOR)
                )
                extra["puede_enviar_revision"] = (
                    est == ch.Estado2daRonda.BORRADOR
                    and puede_transicionar(u, est, ch.Estado2daRonda.PENDIENTE_REVISION)
                )
                extra["puede_marcar_revisado"] = (
                    est == ch.Estado2daRonda.PENDIENTE_REVISION
                    and puede_transicionar(u, est, ch.Estado2daRonda.REVISADO)
                )
                extra["puede_aprobar"] = en_cola and puede_transicionar(
                    u, est, ch.Estado2daRonda.APROBADO
                )
                extra["puede_devolver"] = en_cola and puede_transicionar(
                    u, est, ch.Estado2daRonda.BORRADOR
                )
                extra["puede_publicar"] = (
                    est == ch.Estado2daRonda.APROBADO
                    and puede_transicionar(u, est, ch.Estado2daRonda.PUBLICADO)
                )
                # Visibilidad: admin ve el set completo (habilitados/deshabilitados);
                # el resto solo ve botones que le corresponden en este paso.
                if es_admin:
                    extra["mostrar_iniciar_visita"] = True
                    extra["mostrar_pasar_borrador"] = True
                    extra["mostrar_aprobar"] = True
                    extra["mostrar_devolver"] = True
                    extra["mostrar_enviar_revision"] = True
                    extra["mostrar_marcar_revisado"] = True
                    extra["mostrar_publicar"] = True
                else:
                    extra["mostrar_iniciar_visita"] = extra["puede_iniciar_visita"]
                    extra["mostrar_pasar_borrador"] = extra["puede_pasar_borrador"]
                    extra["mostrar_aprobar"] = extra["puede_aprobar"]
                    extra["mostrar_devolver"] = extra["puede_devolver"]
                    extra["mostrar_enviar_revision"] = extra["puede_enviar_revision"]
                    extra["mostrar_marcar_revisado"] = extra["puede_marcar_revisado"]
                    extra["mostrar_publicar"] = extra["puede_publicar"]
                if es_admin:
                    extra["n_historial_estados"] = caso.historial_estados.count()
                    extra["n_adjuntos_prueba"] = (
                        caso.informes_pdf.count()
                        + caso.croquis.count()
                        + caso.fotos.count()
                        + caso.lineas_metrado.count()
                    )
            except (CasoRojo.DoesNotExist, ValueError, TypeError):
                extra["n_historial_estados"] = 0
                extra["n_adjuntos_prueba"] = 0
                extra["n_fotos_adjuntas"] = 0
                extra["checklist_cierre"] = None
        return super().change_view(request, object_id, form_url, extra_context=extra)

    def save_model(self, request, obj, form, change):
        if not puede_modificar_casos(request.user):
            raise ValidationError("Su usuario es solo consulta: no puede modificar casos.")
        if change and obj.pk and not usuario_puede_ver_caso(request.user, obj):
            raise ValidationError("No tiene permiso sobre este caso.")
        # Impedir que no-admin cambie coordinador_asignado por POST manipulado
        if change and obj.pk and not es_administrador(request.user):
            prev = CasoRojo.objects.filter(pk=obj.pk).values_list(
                "coordinador_asignado_id", flat=True
            ).first()
            obj.coordinador_asignado_id = prev
        if es_solo_revisor(request.user) and change and obj.pk:
            prev_i = CasoRojo.objects.filter(pk=obj.pk).values_list(
                "inspector_asignado_id", flat=True
            ).first()
            prev_r = CasoRojo.objects.filter(pk=obj.pk).values_list(
                "revisor_asignado_id", flat=True
            ).first()
            obj.inspector_asignado_id = prev_i
            obj.revisor_asignado_id = prev_r
        anterior = None
        before_snap = {}
        before_counts = {}
        if change and obj.pk:
            from inspecciones.historial_detalle import counts_adjuntos, snapshot_caso

            prev_obj = CasoRojo.objects.filter(pk=obj.pk).first()
            if prev_obj:
                before_snap = snapshot_caso(prev_obj)
                before_counts = counts_adjuntos(prev_obj)
            anterior = before_snap.get("estado_2da") or (
                CasoRojo.objects.filter(pk=obj.pk).values_list("estado_2da", flat=True).first()
            )
            if anterior and anterior != obj.estado_2da:
                validar_transicion_estado(request.user, anterior, obj.estado_2da)
        from inspecciones import choices as ch

        # La validación de dictamen corre en CasoRojoAdminForm.clean()
        # para conservar el POST si falla («Guardar y continuar»).
        # Aquí solo alinear precarga / GPS y el contador de fotos.
        obj.aplicar_correcciones_a_precarga()
        if obj.estado_2da in (
            ch.Estado2daRonda.PENDIENTE_REVISION,
            ch.Estado2daRonda.REVISADO,
            ch.Estado2daRonda.APROBADO,
            ch.Estado2daRonda.PUBLICADO,
        ):
            obj.n_fotos = str(obj.fotos.count())
        obj.sync_gps_texto()
        super().save_model(request, obj, form, change)
        if change and anterior and anterior != obj.estado_2da:
            nota_est = f"Cambio de estado al guardar ficha: {anterior} → {obj.estado_2da}"
            HistorialEstado.objects.create(
                caso=obj,
                estado_anterior=anterior,
                estado_nuevo=obj.estado_2da,
                usuario=request.user,
                nota=nota_est,
            )
            from inspecciones.historial_detalle import registrar_historial_detallado

            registrar_historial_detallado(
                caso=obj,
                usuario=request.user,
                resumen=nota_est,
                detalle=(
                    f"Estado: {anterior} → {obj.estado_2da}\n"
                    f"Origen: guardado de ficha"
                ),
                origen="accion_estado",
            )
        # Snapshot para completar en save_related (metrados/fotos)
        request._cpeh_audit_before = before_snap
        request._cpeh_audit_before_counts = before_counts
        request._cpeh_audit_is_new = not change

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from inspecciones.historial_detalle import registrar_guardado_ficha, registrar_historial_detallado
        from inspecciones.proc_metrado_sync import sync_procedimientos_metrados

        rows = getattr(form, "_proc_catalog_rows", None) or []
        selected = list(form.cleaned_data.get("procedimientos_catalogo") or [])
        n_sync = sync_procedimientos_metrados(form.instance, request.POST, selected, rows)

        caso = form.instance
        if getattr(request, "_cpeh_audit_is_new", False):
            registrar_historial_detallado(
                caso=caso,
                usuario=request.user,
                resumen="Alta / primer guardado de la ficha",
                detalle=(
                    f"Se creó o guardó por primera vez el caso {caso.hab_id} "
                    f"desde la ficha web."
                ),
                origen="ficha",
            )
            return

        before = getattr(request, "_cpeh_audit_before", None) or {}
        before_counts = getattr(request, "_cpeh_audit_before_counts", None)
        nota_extra = ""
        if n_sync:
            nota_extra = f"Sincronizó {n_sync} línea(s) desde catálogo de procedimientos"
        registrar_guardado_ficha(
            caso=caso,
            usuario=request.user,
            before=before,
            before_counts=before_counts,
            origen="ficha",
            nota_extra=nota_extra,
        )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, EvidenciaFoto) and not inst.subido_por_id:
                inst.subido_por = request.user
            if isinstance(inst, InformePdfAdjunto):
                if not inst.subido_por_id:
                    inst.subido_por = request.user
                if inst.archivo and not inst.nombre_archivo_origen:
                    inst.nombre_archivo_origen = inst.archivo.name.rsplit("/", 1)[-1]
            if isinstance(inst, CroquisAdjunto):
                if not inst.subido_por_id:
                    inst.subido_por = request.user
                if inst.archivo and not inst.nombre_archivo_origen:
                    inst.nombre_archivo_origen = inst.archivo.name.rsplit("/", 1)[-1]
            inst.save()
        formset.save_m2m()
        for inst in formset.deleted_objects:
            inst.delete()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/pdf/",
                self.admin_site.admin_view(self.vista_pdf),
                name="inspecciones_casorojo_pdf",
            ),
            path(
                "cargar-excel/",
                self.admin_site.admin_view(self.vista_cargar_excel_lista),
                name="inspecciones_casorojo_cargar_excel",
            ),
            path(
                "<path:object_id>/resetear-prueba/",
                self.admin_site.admin_view(self.vista_resetear_datos_prueba),
                name="inspecciones_casorojo_resetear_prueba",
            ),
            path(
                "<path:object_id>/aprobar/",
                self.admin_site.admin_view(self.vista_aprobar),
                name="inspecciones_casorojo_aprobar",
            ),
            path(
                "<path:object_id>/devolver-borrador/",
                self.admin_site.admin_view(self.vista_devolver),
                name="inspecciones_casorojo_devolver",
            ),
            path(
                "<path:object_id>/enviar-revision/",
                self.admin_site.admin_view(self.vista_enviar_revision),
                name="inspecciones_casorojo_enviar_revision",
            ),
            path(
                "<path:object_id>/marcar-revisado/",
                self.admin_site.admin_view(self.vista_marcar_revisado),
                name="inspecciones_casorojo_marcar_revisado",
            ),
            path(
                "<path:object_id>/publicar/",
                self.admin_site.admin_view(self.vista_publicar),
                name="inspecciones_casorojo_publicar",
            ),
            path(
                "<path:object_id>/iniciar-visita/",
                self.admin_site.admin_view(self.vista_iniciar_visita),
                name="inspecciones_casorojo_iniciar_visita",
            ),
            path(
                "<path:object_id>/pasar-borrador/",
                self.admin_site.admin_view(self.vista_pasar_borrador),
                name="inspecciones_casorojo_pasar_borrador",
            ),
        ]
        return custom + urls

    def vista_aprobar(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="aprobar")

    def vista_devolver(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="devolver")

    def vista_enviar_revision(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="enviar_revision")

    def vista_marcar_revisado(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="marcar_revisado")

    def vista_publicar(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="publicar")

    def vista_iniciar_visita(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="iniciar_visita")

    def vista_pasar_borrador(self, request, object_id):
        return self.vista_cambiar_estado(request, object_id, accion="pasar_borrador")

    def vista_cambiar_estado(self, request, object_id, accion: str = "aprobar"):
        """Botones didácticos de flujo (estado + rol vía validar_transicion_estado)."""
        from django.http import HttpResponseForbidden, HttpResponseRedirect

        from inspecciones import choices as ch

        caso = get_object_or_404(CasoRojo, pk=object_id)
        change_url = reverse("admin:inspecciones_casorojo_change", args=[caso.pk])

        if not usuario_puede_ver_caso(request.user, caso):
            return HttpResponseForbidden("No tiene permiso sobre este caso.")
        if not puede_modificar_casos(request.user):
            return HttpResponseForbidden("Usuario solo consulta: no puede cambiar estados.")
        if request.method != "POST":
            messages.warning(request, "Use el botón de la ficha (requiere confirmación).")
            return HttpResponseRedirect(change_url)

        mapa = {
            "iniciar_visita": (
                ch.Estado2daRonda.EN_VISITA,
                "Marcado En visita desde ficha",
            ),
            "pasar_borrador": (
                ch.Estado2daRonda.BORRADOR,
                "Pasado a Borrador desde ficha (informe en elaboración)",
            ),
            "aprobar": (ch.Estado2daRonda.APROBADO, "Aprobado desde ficha (botón Aprobar)"),
            "devolver": (ch.Estado2daRonda.BORRADOR, "Devuelto a borrador desde ficha"),
            "enviar_revision": (
                ch.Estado2daRonda.PENDIENTE_REVISION,
                "Enviado a Pendiente revisión desde ficha",
            ),
            "marcar_revisado": (
                ch.Estado2daRonda.REVISADO,
                "Marcado como Revisado (control técnico confirmado)",
            ),
            "publicar": (ch.Estado2daRonda.PUBLICADO, "Publicado desde ficha"),
        }
        if accion not in mapa:
            messages.error(request, "Acción de estado desconocida.")
            return HttpResponseRedirect(change_url)

        nuevo, nota = mapa[accion]
        # Defensa en profundidad (la validación de grafo/rol es la fuente de verdad)
        # Aprobar / marcar Revisado: solo revisor técnico o admin (NO coordinador).
        if accion in ("aprobar", "marcar_revisado") and not (
            es_administrador(request.user) or es_solo_revisor(request.user)
        ):
            return HttpResponseForbidden(
                "Solo revisor técnico o administrador pueden confirmar revisión o aprobar."
            )
        if accion == "publicar" and not (
            es_administrador(request.user) or es_coordinador(request.user)
        ):
            return HttpResponseForbidden("Solo coordinador o admin pueden publicar.")

        anterior = caso.estado_2da
        try:
            validar_transicion_estado(request.user, anterior, nuevo)
            caso.estado_2da = nuevo
            cerrar = nuevo in (
                ch.Estado2daRonda.PENDIENTE_REVISION,
                ch.Estado2daRonda.REVISADO,
                ch.Estado2daRonda.APROBADO,
                ch.Estado2daRonda.PUBLICADO,
            )
            if cerrar:
                caso.n_fotos = str(caso.fotos.count())
            validar_dictamen(caso, cerrar=cerrar)
            caso.save()
            HistorialEstado.objects.create(
                caso=caso,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                usuario=request.user,
                nota=nota,
            )
            from inspecciones.historial_detalle import registrar_historial_detallado

            registrar_historial_detallado(
                caso=caso,
                usuario=request.user,
                resumen=nota,
                detalle=(
                    f"Acción de flujo desde ficha.\n"
                    f"Estado: {anterior} → {nuevo}\n"
                    f"Nota: {nota}"
                ),
                origen="accion_estado",
            )
        except ValidationError as exc:
            messages.error(request, f"No se pudo cambiar el estado: {exc}")
            return HttpResponseRedirect(change_url)

        etiquetas = {
            "iniciar_visita": "marcado En visita",
            "pasar_borrador": "pasado a Borrador",
            "aprobar": "aprobado",
            "devolver": "devuelto a borrador",
            "enviar_revision": "enviado a Pendiente revisión",
            "marcar_revisado": "marcado como Revisado",
            "publicar": "publicado",
        }
        messages.success(
            request,
            f"Caso {caso.hab_id} {etiquetas.get(accion, 'actualizado')}: "
            f"«{anterior}» → «{nuevo}».",
        )
        return HttpResponseRedirect(change_url)

    def vista_pdf(self, request, object_id):
        from inspecciones.views import caso_rojo_pdf

        caso = get_object_or_404(CasoRojo, pk=object_id)
        return caso_rojo_pdf(request, caso.pk)

    def vista_cargar_excel_lista(self, request):
        from inspecciones.import_views import cargar_excel_informe

        return cargar_excel_informe(request, pk=None)

    def vista_resetear_datos_prueba(self, request, object_id):
        """Limpia visita/Excel/adjuntos/historial; conserva precarga. Solo admin."""
        from django.http import HttpResponseForbidden, HttpResponseRedirect

        if not es_administrador(request.user):
            return HttpResponseForbidden(
                "Solo el administrador puede resetear datos de prueba."
            )
        caso = get_object_or_404(CasoRojo, pk=object_id)
        if request.method != "POST":
            messages.warning(
                request,
                "Use el botón «Resetear datos de prueba» en la ficha (requiere confirmación).",
            )
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
            )
        try:
            counts = caso.resetear_datos_prueba()
        except Exception as exc:
            messages.error(
                request,
                f"Error al resetear caso {caso.hab_id}: {exc}",
            )
            return HttpResponseRedirect(
                reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
            )
        messages.success(
            request,
            (
                f"Caso {caso.hab_id} reseteado para pruebas. "
                f"Precarga (Habitable/ranking) conservada. "
                f"Limpiado: historial {counts['historial']}, "
                f"PDF {counts['informes_pdf']}, croquis {counts['croquis']}, "
                f"fotos {counts['fotos']}, metrados {counts['metrados']}. "
                f"Estado → Pendiente verificación."
            ),
        )
        return HttpResponseRedirect(
            reverse("admin:inspecciones_casorojo_change", args=[caso.pk])
        )

    fieldsets = CASE_FIELDSETS

    def get_fieldsets(self, request, obj=None):
        return get_case_fieldsets_admin()


@admin.register(Procedimiento)
class ProcedimientoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "categoria",
        "titulo",
        "activo",
        "descargar_pdf",
        "descargar_cad",
    )
    list_filter = ("categoria", "activo")
    search_fields = ("codigo", "titulo", "descripcion")
    ordering = ("categoria", "codigo")
    actions = ("asegurar_catalogo",)

    @admin.display(description="PDF")
    def descargar_pdf(self, obj: Procedimiento) -> str:
        from django.urls import reverse
        from django.utils.html import format_html

        url = reverse("ficha_procedimiento_pdf", args=[obj.codigo])
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">Descargar</a>',
            url,
        )

    @admin.display(description="CAD")
    def descargar_cad(self, obj: Procedimiento) -> str:
        from django.urls import reverse
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe

        if (obj.codigo or "").strip().upper() != "PLN-01":
            return mark_safe("—")
        url = reverse("ficha_procedimiento_dxf", args=[obj.codigo])
        return format_html(
            '<a class="button" href="{}" rel="noopener">DXF</a>',
            url,
        )

    @admin.action(description="Sincronizar catálogo semilla (incl. PLN-01)")
    def asegurar_catalogo(self, request, queryset):
        from inspecciones.catalogo_procedimientos import asegurar_procedimientos_catalogo

        n = asegurar_procedimientos_catalogo()
        self.message_user(request, f"Catálogo sincronizado. Nuevos creados: {n}.")


@admin.register(PartidaCatalogo)
class PartidaCatalogoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "grupo",
        "titulo",
        "unidad_default",
        "precio_unitario",
        "moneda",
        "aplica_decisiones",
        "activo",
        "orden",
    )
    list_filter = ("grupo", "activo", "unidad_default")
    search_fields = ("codigo", "titulo", "descripcion")
    ordering = ("orden", "grupo", "codigo")
    list_editable = ("precio_unitario", "activo", "orden")


@admin.register(LineaMetrado)
class LineaMetradoAdmin(admin.ModelAdmin):
    list_display = (
        "caso",
        "orden",
        "codigo_partida",
        "id_pln01",
        "elemento",
        "cantidad",
        "unidad",
        "tipo_apuntamiento",
        "accion",
        "severidad",
    )
    list_filter = ("accion", "unidad", "severidad", "tipo_apuntamiento")
    search_fields = ("caso__hab_id", "codigo_partida", "id_pln01", "ubicacion", "nota")
    autocomplete_fields = ("caso", "partida")


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ("caso", "estado_anterior", "estado_nuevo", "usuario", "nota", "created_at")
    list_filter = ("estado_nuevo",)
    search_fields = ("caso__hab_id", "caso__nombre_hab", "nota")
    readonly_fields = ("caso", "estado_anterior", "estado_nuevo", "usuario", "nota", "created_at")
    actions = ("borrar_seleccionados",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if ve_todos_los_casos(request.user):
            return qs
        casos = filtrar_casos_por_rol(request.user)
        return qs.filter(caso__in=casos)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not es_administrador(request.user):
            actions.pop("borrar_seleccionados", None)
            actions.pop("delete_selected", None)
        return actions

    @admin.action(description="[Admin] Borrar registros de historial seleccionados")
    def borrar_seleccionados(self, request, queryset):
        if not es_administrador(request.user):
            self.message_user(request, "Solo administrador.", level=messages.ERROR)
            return
        n = queryset.count()
        queryset.delete()
        self.message_user(request, f"Se borraron {n} registro(s) de historial.", level=messages.SUCCESS)


@admin.register(HistorialDetallado)
class HistorialDetalladoAdmin(admin.ModelAdmin):
    list_display = ("caso", "resumen", "usuario", "origen", "created_at")
    list_filter = ("origen",)
    search_fields = ("caso__hab_id", "caso__nombre_hab", "resumen", "detalle")
    readonly_fields = ("caso", "usuario", "resumen", "detalle", "origen", "created_at")
    actions = ("borrar_seleccionados",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if ve_todos_los_casos(request.user):
            return qs
        casos = filtrar_casos_por_rol(request.user)
        return qs.filter(caso__in=casos)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not es_administrador(request.user):
            actions.pop("borrar_seleccionados", None)
            actions.pop("delete_selected", None)
        return actions

    @admin.action(description="[Admin] Borrar entradas de historial detallado")
    def borrar_seleccionados(self, request, queryset):
        if not es_administrador(request.user):
            self.message_user(request, "Solo administrador.", level=messages.ERROR)
            return
        n = queryset.count()
        queryset.delete()
        self.message_user(request, f"Se borraron {n} entrada(s) de historial detallado.", level=messages.SUCCESS)
        n, _ = queryset.delete()
        self.message_user(request, f"Eliminados {n} registro(s) de historial.", level=messages.SUCCESS)


@admin.register(EvidenciaFoto)
class EvidenciaFotoAdmin(admin.ModelAdmin):
    list_display = ("caso", "descripcion", "subido_por", "created_at")
    list_filter = ("created_at",)
    search_fields = ("caso__hab_id", "descripcion")
    autocomplete_fields = ("caso",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if ve_todos_los_casos(request.user):
            return qs
        return qs.filter(caso__in=filtrar_casos_por_rol(request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "caso" and not ve_todos_los_casos(request.user):
            kwargs["queryset"] = filtrar_casos_por_rol(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return puede_modificar_casos(request.user) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_delete_permission(
            request, obj
        )


@admin.register(InformePdfAdjunto)
class InformePdfAdjuntoAdmin(admin.ModelAdmin):
    list_display = ("caso", "titulo", "tipo_informe", "nombre_archivo_origen", "subido_por", "created_at", "enlace_ver")
    list_filter = ("tipo_informe", "created_at")
    search_fields = ("caso__hab_id", "titulo", "nombre_archivo_origen", "codigo_documento")
    autocomplete_fields = ("caso",)
    fields = (
        "caso",
        "archivo",
        "titulo",
        "tipo_informe",
        "codigo_documento",
        "nombre_archivo_origen",
        "notas",
        "subido_por",
        "created_at",
    )
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if ve_todos_los_casos(request.user):
            return qs
        return qs.filter(caso__in=filtrar_casos_por_rol(request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "caso" and not ve_todos_los_casos(request.user):
            kwargs["queryset"] = filtrar_casos_por_rol(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return puede_modificar_casos(request.user) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_delete_permission(
            request, obj
        )

    @admin.display(description="PDF")
    def enlace_ver(self, obj: InformePdfAdjunto) -> str:
        if obj.pk and obj.archivo:
            url = reverse("ver_informe_pdf_adjunto", args=[obj.pk])
            return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', url)
        return "—"

    def save_model(self, request, obj, form, change):
        if not puede_modificar_casos(request.user):
            raise ValidationError("Usuario solo consulta: no puede adjuntar informes.")
        if not obj.subido_por_id:
            obj.subido_por = request.user
        if obj.archivo and not obj.nombre_archivo_origen:
            obj.nombre_archivo_origen = obj.archivo.name.rsplit("/", 1)[-1]
        super().save_model(request, obj, form, change)


@admin.register(CroquisAdjunto)
class CroquisAdjuntoAdmin(admin.ModelAdmin):
    list_display = (
        "caso",
        "codigo_piso",
        "titulo",
        "nombre_archivo_origen",
        "subido_por",
        "created_at",
        "enlace_ver",
    )
    list_filter = ("codigo_piso", "created_at")
    search_fields = ("caso__hab_id", "titulo", "codigo_piso", "nombre_archivo_origen", "notas")
    autocomplete_fields = ("caso",)
    fields = (
        "caso",
        "codigo_piso",
        "archivo",
        "titulo",
        "notas",
        "nombre_archivo_origen",
        "subido_por",
        "created_at",
    )
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if ve_todos_los_casos(request.user):
            return qs
        return qs.filter(caso__in=filtrar_casos_por_rol(request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "caso" and not ve_todos_los_casos(request.user):
            kwargs["queryset"] = filtrar_casos_por_rol(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return puede_modificar_casos(request.user) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return puede_modificar_casos(request.user) and super().has_delete_permission(
            request, obj
        )

    @admin.display(description="Archivo")
    def enlace_ver(self, obj: CroquisAdjunto) -> str:
        if obj.pk and obj.archivo:
            url = reverse("ver_croquis_adjunto", args=[obj.pk])
            return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', url)
        return "—"

    def save_model(self, request, obj, form, change):
        if not puede_modificar_casos(request.user):
            raise ValidationError("Usuario solo consulta: no puede adjuntar croquis.")
        if not obj.subido_por_id:
            obj.subido_por = request.user
        if obj.archivo and not obj.nombre_archivo_origen:
            obj.nombre_archivo_origen = obj.archivo.name.rsplit("/", 1)[-1]
        super().save_model(request, obj, form, change)


@admin.register(PlantaInspeccion)
class PlantaInspeccionAdmin(admin.ModelAdmin):
    list_display = ("caso", "orden", "codigo_piso", "titulo", "activa", "croquis")
    list_filter = ("activa", "codigo_piso")
    search_fields = ("caso__hab_id", "codigo_piso", "titulo")
    autocomplete_fields = ("caso", "croquis")
    ordering = ("caso", "orden", "codigo_piso")


@admin.register(EquipoBrigada)
class EquipoBrigadaAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre", "activo", "updated_at")
    list_editable = ("nombre", "activo")
    list_display_links = ("numero",)
    search_fields = ("nombre", "notas")
    ordering = ("numero",)

    def has_module_permission(self, request):
        return es_administrador(request.user)

    def has_view_permission(self, request, obj=None):
        return es_administrador(request.user)

    def has_add_permission(self, request):
        return es_administrador(request.user)

    def has_change_permission(self, request, obj=None):
        return es_administrador(request.user)

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)


@admin.register(CredencialEmitida)
class CredencialEmitidaAdmin(admin.ModelAdmin):
    list_display = ("user", "password_plain", "emitida_en", "emitida_por")
    search_fields = ("user__username", "password_plain")
    readonly_fields = ("user", "password_plain", "emitida_en", "emitida_por", "nota")

    def has_module_permission(self, request):
        return es_administrador(request.user)

    def has_view_permission(self, request, obj=None):
        return es_administrador(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)
