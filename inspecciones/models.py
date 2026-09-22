"""Modelo consolidado Fase II — secciones numeradas (informe / Excel / anteproyecto)."""
from django.conf import settings
from django.db import models

from . import choices as ch


class CasoRojo(models.Model):
    """Un caso ROJO en 2.ª ronda (informe consolidado en una fila administrable)."""

    # --- 1 Precarga Habitable ---
    hab_id = models.PositiveIntegerField("ID Habitable", unique=True, db_index=True)
    certificado = models.CharField(max_length=64, blank=True)
    nombre_hab = models.CharField("Nombre (Habitable)", max_length=255, blank=True)
    etiqueta_f1 = models.CharField("Etiqueta Fase 1", max_length=20, default="ROJO")
    fecha_f1 = models.DateField("Fecha inspección Fase 1", null=True, blank=True)
    inspector_f1 = models.CharField("Inspector Fase 1", max_length=255, blank=True)
    direccion_hab = models.CharField("Dirección Habitable", max_length=500, blank=True)
    muni_parr = models.CharField("Municipio / Parroquia", max_length=255, blank=True)
    pisos_f1 = models.CharField("Pisos / sótanos (Fase 1)", max_length=64, blank=True)
    riesgos_f1 = models.CharField("Riesgo externo / severo", max_length=128, blank=True)
    colapso_f1 = models.CharField("Colapso estructura (Fase 1)", max_length=16, blank=True)
    piso_crit_f1 = models.CharField("Piso crítico (Fase 1)", max_length=255, blank=True)
    acciones_f1 = models.CharField("Acciones Fase 1", max_length=255, blank=True)
    obs_f1 = models.TextField("Observaciones Fase 1", blank=True)
    gps_hab = models.CharField("GPS Habitable", max_length=64, blank=True)
    lat = models.DecimalField("Latitud", max_digits=10, decimal_places=7, null=True, blank=True, db_index=True)
    lng = models.DecimalField("Longitud", max_digits=10, decimal_places=7, null=True, blank=True, db_index=True)

    # --- 2 Ranking ---
    score = models.PositiveSmallIntegerField("Score gravedad (0–100)", null=True, blank=True)
    banda = models.CharField("Banda prioridad", max_length=32, blank=True)
    puestos = models.CharField("Puesto La Guaira / nacional", max_length=64, blank=True)
    score_detalle = models.TextField("Detalle del score", blank=True)
    prob_rel = models.CharField("Probabilidad relativa (texto)", max_length=255, blank=True)

    # --- 3 Validación ---
    val_edificio = models.CharField(
        max_length=32, choices=ch.SiNoParcial.choices, default=ch.SiNoParcial.PENDIENTE, blank=True
    )
    val_etiqueta = models.CharField(
        max_length=32, choices=ch.SiNoInsuf.choices, default=ch.SiNoInsuf.PENDIENTE, blank=True
    )
    val_geometria = models.CharField(
        max_length=32, choices=ch.SiNoParcial.choices, default=ch.SiNoParcial.PENDIENTE, blank=True
    )
    val_ranking = models.CharField(
        max_length=32, choices=ch.SiNoParcial.choices, default=ch.SiNoParcial.PENDIENTE, blank=True
    )
    # Valores correctos (si marcó No / Parcial): se aplican a la precarga y al Excel
    corr_nombre = models.CharField(
        "Nombre correcto",
        max_length=255,
        blank=True,
        help_text="Si corrige edificio: reemplaza el nombre Habitable (y el confirmado si está vacío).",
    )
    corr_direccion = models.CharField(
        "Dirección correcta",
        max_length=500,
        blank=True,
        help_text="Reemplaza la dirección de precarga al guardar.",
    )
    corr_muni_parr = models.CharField(
        "Municipio / parroquia correctos",
        max_length=255,
        blank=True,
        help_text="Reemplaza municipio/parroquia de precarga al guardar.",
    )
    corr_etiqueta = models.CharField(
        "Etiqueta correcta (Fase 1)",
        max_length=20,
        blank=True,
        help_text="Ej. ROJO. Reemplaza etiqueta_f1 al guardar.",
    )
    corr_pisos = models.CharField(
        "Pisos / sótanos correctos",
        max_length=64,
        blank=True,
        help_text="Ej. 10 / 2. Reemplaza pisos_f1 (y pisos_conf si vacío).",
    )
    corr_gps = models.CharField(
        "GPS correcto (Habitable)",
        max_length=64,
        blank=True,
        help_text="Reemplaza gps_hab al guardar. El GPS de visita 2 se captura aparte.",
    )
    corr_score = models.PositiveSmallIntegerField(
        "Score correcto (0–100)",
        null=True,
        blank=True,
        help_text="Solo si el ranking/score estaba mal. Reemplaza score al guardar.",
    )
    corr_banda = models.CharField(
        "Banda correcta",
        max_length=32,
        blank=True,
        help_text="Reemplaza banda de prioridad al guardar.",
    )
    correcciones = models.TextField(
        "Nota adicional de corrección",
        blank=True,
        help_text="Opcional si ya llenó los campos «… correcto». Use esto para matices o varios edificios.",
    )

    # --- Asignación operativa ---
    coordinador_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_coordinacion",
        verbose_name="Coordinador asignado",
        help_text="Administrador asigna el caso al coordinador; este a su vez asigna ingenieros.",
    )
    inspector_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_inspeccion",
        verbose_name="Inspector asignado",
    )
    revisor_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_revision",
        verbose_name="Revisor asignado",
    )

    # --- 4 Identidad y edificio (visita 2) ---
    nombre_conf = models.CharField("Nombre confirmado", max_length=255, blank=True)
    fecha_v2 = models.DateField("Fecha visita detallada", null=True, blank=True)
    gps_v2 = models.CharField("GPS control (visita)", max_length=64, blank=True)
    evaluadores_v2 = models.CharField("Evaluadores visita 2", max_length=500, blank=True)
    supervisor_v2 = models.CharField("Supervisor", max_length=255, blank=True)
    uso = models.CharField("Uso", max_length=128, blank=True)
    pisos_conf = models.CharField("Pisos confirmados", max_length=16, blank=True)
    sotanos_conf = models.CharField("Sótanos confirmados", max_length=16, blank=True)
    sistema = models.CharField(
        max_length=64, choices=ch.SistemaEstructural.choices, default=ch.SistemaEstructural.PENDIENTE, blank=True
    )
    ocupacion = models.CharField(
        max_length=32, choices=ch.Ocupacion.choices, default=ch.Ocupacion.PENDIENTE, blank=True
    )
    peligro_aledanos = models.CharField(
        max_length=32, choices=ch.PeligroAledanos.choices, default=ch.PeligroAledanos.PENDIENTE, blank=True
    )

    # --- 5 Daño detallado ---
    piso_crit_v2 = models.CharField("Piso crítico (visita 2)", max_length=255, blank=True)
    pct_columnas = models.CharField(
        max_length=32, choices=ch.PctColumnas.choices, default=ch.PctColumnas.PENDIENTE, blank=True
    )
    inclinacion = models.CharField(
        max_length=32, choices=ch.Inclinacion.choices, default=ch.Inclinacion.PENDIENTE, blank=True
    )
    delta_incl = models.CharField("Δ inclinación (si midió)", max_length=64, blank=True)
    dano_vigas = models.CharField(
        "Daño vigas (síntesis)",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    dano_losas = models.CharField(
        "Daño losas (síntesis)",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
        help_text="Si las losas están comprometidas en varios niveles, márquelo aquí y detalle en §6.",
    )
    riesgo_fachada = models.CharField(
        "Riesgo fachada (síntesis)",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    analisis_libre = models.TextField("Análisis libre (ingeniero)", blank=True)

    # --- 6 Daño estructural (detalle) ---
    col_mec = models.CharField("Columnas — mecanismo", max_length=255, blank=True)
    col_nivel = models.CharField(
        "Columnas — nivel A/B/C",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    col_evidencia = models.TextField("Columnas — ubicación / evidencia", blank=True)
    vig_mec = models.CharField("Vigas — mecanismo", max_length=255, blank=True)
    vig_nivel = models.CharField(
        "Vigas — nivel A/B/C",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    vig_evidencia = models.TextField("Vigas — ubicación / evidencia", blank=True)
    mur_mec = models.CharField("Muros/pantallas — mecanismo", max_length=255, blank=True)
    mur_nivel = models.CharField(
        "Muros/pantallas — nivel A/B/C",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    mur_evidencia = models.TextField("Muros/pantallas — ubicación / evidencia", blank=True)
    los_mec = models.CharField("Losas — mecanismo", max_length=255, blank=True)
    los_nivel = models.CharField(
        "Losas — nivel A/B/C",
        max_length=16,
        choices=ch.NivelABC.choices,
        default=ch.NivelABC.PENDIENTE,
        blank=True,
    )
    los_evidencia = models.TextField(
        "Losas — ubicación / evidencia",
        blank=True,
        help_text="Indique pisos/niveles afectados (ej. losa entrepiso 3–5, zona central).",
    )
    escaleras = models.TextField("Escaleras / evacuación", blank=True)
    preexistentes = models.TextField("Daños preexistentes (pre 24/06/2026)", blank=True)

    # --- 7 Mampostería ---
    mam_mec = models.CharField("Mampostería — mecanismo", max_length=255, blank=True)
    mam_nivel = models.CharField(
        max_length=16, choices=ch.NivelABC.choices, default=ch.NivelABC.PENDIENTE, blank=True
    )
    mam_diag = models.TextField("Diagnóstico mampostería", blank=True)

    # --- 8 Procedimientos sugeridos ---
    proc_codigos = models.TextField("Procedimientos seleccionados (códigos)", blank=True)
    repar_viable = models.CharField(
        max_length=32, choices=ch.SiNoInsuf.choices, default=ch.SiNoInsuf.PENDIENTE, blank=True
    )
    proc_notas = models.TextField("Notas procedimientos", blank=True)

    # --- 9 Cuantificación (metrados / totales para anteproyecto y costos) ---
    area_aprox_m2 = models.DecimalField(
        "Área aproximada construida (m²)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimación para costo grueso y anteproyecto.",
    )
    n_viviendas = models.PositiveIntegerField(
        "N.º viviendas / unidades",
        null=True,
        blank=True,
    )
    vol_escombros_m3 = models.DecimalField(
        "Volumen estimado escombros (m³)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Relevante sobre todo en D3/D4.",
    )
    m_fachada_riesgo = models.DecimalField(
        "Fachada en riesgo (m lineales o m²)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    niveles_intervenir = models.CharField(
        "Niveles a intervenir",
        max_length=64,
        blank=True,
        help_text="Ej. 1–4, sótano+PB, todos.",
    )
    pct_estructura_intervenir = models.CharField(
        "% estructura a intervenir",
        max_length=32,
        choices=ch.PctColumnas.choices,
        default=ch.PctColumnas.PENDIENTE,
        blank=True,
    )
    metrado_confianza = models.CharField(
        "Confianza global del metrado",
        max_length=16,
        choices=ch.ConfianzaMetrado.choices,
        default=ch.ConfianzaMetrado.PENDIENTE,
        blank=True,
    )
    metrado_notas = models.TextField(
        "Notas de cuantificación",
        blank=True,
        help_text="Supuestos del levantamiento; no sustituye las líneas de metrado.",
    )

    # --- 10 Decisión de control ---
    estado_2da = models.CharField(
        max_length=32,
        choices=ch.Estado2daRonda.choices,
        default=ch.Estado2daRonda.PENDIENTE,
        blank=True,
    )
    decision_D = models.CharField(
        max_length=64, choices=ch.DecisionD.choices, default=ch.DecisionD.PENDIENTE, blank=True
    )
    complementos_D = models.CharField(
        "Complementos requeridos (D1)",
        max_length=128,
        blank=True,
        help_text="Códigos separados por coma: GEO, ENS, MOD, MON, INV, REI, ALE, OTR.",
    )
    complemento_plazo = models.DateField("Plazo / fecha objetivo (D1)", null=True, blank=True)
    complemento_detalle = models.TextField(
        "Detalle complemento — qué falta y entregable (D1)",
        blank=True,
    )
    magnitud_M = models.CharField(
        max_length=64, choices=ch.MagnitudM.choices, default=ch.MagnitudM.PENDIENTE, blank=True
    )
    prioridad = models.CharField(
        max_length=32, choices=ch.PrioridadOperativa.choices, default=ch.PrioridadOperativa.PENDIENTE, blank=True
    )
    medidas = models.TextField("Medidas inmediatas", blank=True)
    justificacion = models.TextField("Justificación libre", blank=True)

    # --- 11 Evidencia ---
    n_fotos = models.CharField("N.º de fotos", max_length=128, blank=True)
    firmas = models.CharField("Firmas (elaboró / revisó / aprobó)", max_length=500, blank=True)

    # --- 12 Resumen ---
    resumen_ejecutivo = models.TextField("Resumen ejecutivo", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Caso ROJO Fase II"
        verbose_name_plural = "Casos ROJO Fase II"
        ordering = ["-score", "hab_id"]

    def __str__(self) -> str:
        nombre = self.nombre_conf or self.nombre_hab or f"ID {self.hab_id}"
        return f"{self.hab_id} — {nombre}"

    # Mapeo: campo corrección → campo precarga (y opcionalmente visita)
    CORRECCION_MAPA = (
        ("corr_nombre", "nombre_hab", "Nombre"),
        ("corr_direccion", "direccion_hab", "Dirección"),
        ("corr_muni_parr", "muni_parr", "Municipio/parroquia"),
        ("corr_etiqueta", "etiqueta_f1", "Etiqueta F1"),
        ("corr_pisos", "pisos_f1", "Pisos/sótanos"),
        ("corr_gps", "gps_hab", "GPS Habitable"),
        ("corr_score", "score", "Score"),
        ("corr_banda", "banda", "Banda"),
    )

    def correcciones_estructuradas_llenas(self) -> bool:
        if (self.corr_nombre or "").strip():
            return True
        if (self.corr_direccion or "").strip():
            return True
        if (self.corr_muni_parr or "").strip():
            return True
        if (self.corr_etiqueta or "").strip():
            return True
        if (self.corr_pisos or "").strip():
            return True
        if (self.corr_gps or "").strip():
            return True
        if self.corr_score is not None:
            return True
        if (self.corr_banda or "").strip():
            return True
        return False

    def aplicar_correcciones_a_precarga(self) -> list[str]:
        """
        Copia valores «correctos» a la precarga (secc. 1–2).
        Devuelve líneas de bitácora para la nota de corrección.
        """
        lineas: list[str] = []
        for origen, destino, etiqueta in self.CORRECCION_MAPA:
            nuevo = getattr(self, origen, None)
            if nuevo is None:
                continue
            if isinstance(nuevo, str) and not nuevo.strip():
                continue
            anterior = getattr(self, destino, None)
            if str(anterior or "") == str(nuevo):
                continue
            setattr(self, destino, nuevo)
            lineas.append(f"{etiqueta}: «{anterior or '—'}» → «{nuevo}»")

        # Alinear visita 2 si aún no se confirmó
        if (self.corr_nombre or "").strip() and not (self.nombre_conf or "").strip():
            self.nombre_conf = self.corr_nombre.strip()
        if (self.corr_pisos or "").strip() and not (self.pisos_conf or "").strip():
            self.pisos_conf = self.corr_pisos.strip()

        if lineas:
            auto = "Correcciones aplicadas a precarga (también en Excel):\n- " + "\n- ".join(lineas)
            nota = (self.correcciones or "").strip()
            # Evitar duplicar el bloque automático si el usuario re-guarda
            if nota.startswith("Correcciones aplicadas a precarga"):
                # conservar solo la parte libre tras el bloque, si la hubiera
                partes = nota.split("\n\n", 1)
                nota = partes[1].strip() if len(partes) > 1 else ""
            self.correcciones = auto + (f"\n\n{nota}" if nota else "")
        return lineas

    # Precarga ranking + asignación: no se tocan al resetear pruebas.
    CAMPOS_CONSERVAR_RESET_PRUEBA = frozenset(
        {
            "id",
            "hab_id",
            "created_at",
            "updated_at",
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
            "lat",
            "lng",
            "score",
            "banda",
            "puestos",
            "score_detalle",
            "prob_rel",
            "uso",  # viene del ranking
            "coordinador_asignado",
            "inspector_asignado",
            "revisor_asignado",
        }
    )

    def resetear_datos_prueba(self) -> dict[str, int]:
        """
        Deja el caso como tras la precarga: limpia visita/Excel/adjuntos/historial.
        Conserva secciones 1–2 (ranking), coordenadas y asignación de roles.
        No restaura precarga ya mutada por corr_* (haría falta reimportar ranking).
        """
        from django.db import transaction

        counts = {
            "historial": 0,
            "historial_detallado": 0,
            "metrados": 0,
            "informes_pdf": 0,
            "croquis": 0,
            "fotos": 0,
            "campos": 0,
        }

        def _borrar_con_archivo(qs, file_attr: str) -> int:
            n = 0
            for obj in qs.iterator():
                f = getattr(obj, file_attr, None)
                if f:
                    try:
                        f.delete(save=False)
                    except Exception:
                        pass
                obj.delete()
                n += 1
            return n

        with transaction.atomic():
            counts["historial"] = self.historial_estados.count()
            self.historial_estados.all().delete()
            counts["historial_detallado"] = self.historial_detallado.count()
            self.historial_detallado.all().delete()
            counts["metrados"] = self.lineas_metrado.count()
            self.lineas_metrado.all().delete()
            counts["informes_pdf"] = _borrar_con_archivo(self.informes_pdf.all(), "archivo")
            counts["croquis"] = _borrar_con_archivo(self.croquis.all(), "archivo")
            counts["fotos"] = _borrar_con_archivo(self.fotos.all(), "imagen")

            for field in self._meta.fields:
                name = field.name
                if name in self.CAMPOS_CONSERVAR_RESET_PRUEBA:
                    continue
                if field.primary_key or field.auto_created:
                    continue
                if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                    continue

                if field.has_default():
                    default = field.get_default()
                    if callable(default):
                        default = default()
                    setattr(self, name, default)
                elif field.null:
                    setattr(self, name, None)
                elif isinstance(field, (models.CharField, models.TextField)):
                    setattr(self, name, "")
                else:
                    continue
                counts["campos"] += 1

            # Estado explícito: listo para nueva prueba (como precarga fresca)
            self.estado_2da = ch.Estado2daRonda.PENDIENTE
            self.save()

        return counts

    def sync_gps_texto(self) -> None:
        if self.lat is not None and self.lng is not None and not self.gps_hab:
            self.gps_hab = f"{self.lat}, {self.lng}"


class InformePdfAdjunto(models.Model):
    """Informe PDF en formato libre (original de campo / escaneado)."""

    caso = models.ForeignKey(
        CasoRojo,
        on_delete=models.CASCADE,
        related_name="informes_pdf",
        verbose_name="Caso ROJO",
    )
    archivo = models.FileField(
        "Archivo PDF",
        upload_to="informes/%Y/%m/",
        help_text="Informe técnico original en PDF (cualquier formato / plantilla).",
    )
    titulo = models.CharField("Título / referencia", max_length=255, blank=True)
    nombre_archivo_origen = models.CharField("Nombre archivo origen", max_length=255, blank=True)
    tipo_informe = models.CharField("Tipo de informe", max_length=128, blank=True)
    codigo_documento = models.CharField("Código documento", max_length=64, blank=True)
    notas = models.TextField("Notas", blank=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="informes_pdf_subidos",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Informe PDF adjunto"
        verbose_name_plural = "Informes PDF adjuntos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        ref = self.titulo or self.nombre_archivo_origen or f"PDF #{self.pk}"
        return f"{self.caso.hab_id} — {ref}"


class CategoriaProcedimiento(models.TextChoices):
    VIG = "VIG", "Vigas"
    COL = "COL", "Columnas"
    MAM = "MAM", "Mampostería"
    OTRO = "OTRO", "Otro"


class Procedimiento(models.Model):
    """Catálogo de procedimientos de reparación (referencia técnica)."""

    codigo = models.CharField("Código", max_length=16, unique=True)
    categoria = models.CharField(max_length=8, choices=CategoriaProcedimiento.choices)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Procedimiento"
        verbose_name_plural = "Catálogo de procedimientos"
        ordering = ["categoria", "codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} — {self.titulo}"


class PartidaCatalogo(models.Model):
    """Catálogo paramétrico de partidas para metrados y futuros costos unitarios."""

    codigo = models.CharField("Código partida", max_length=32, unique=True, db_index=True)
    grupo = models.CharField(max_length=16, choices=ch.GrupoPartida.choices, default=ch.GrupoPartida.OTRO)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    unidad_default = models.CharField(
        max_length=16, choices=ch.UnidadMetrado.choices, default=ch.UnidadMetrado.UND
    )
    precio_unitario = models.DecimalField(
        "Precio unitario (opcional)",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Vacío por ahora; cuando se cargue, habilita costo estimado = cantidad × PU.",
    )
    moneda = models.CharField(max_length=8, default="USD", blank=True)
    aplica_decisiones = models.CharField(
        "Aplica a decisiones",
        max_length=64,
        blank=True,
        help_text="Ej. D2,D3 o D1,D2 (vacío = todas).",
    )
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=100)

    class Meta:
        verbose_name = "Partida de metrado (catálogo)"
        verbose_name_plural = "Catálogo de partidas (metrados / costos)"
        ordering = ["orden", "grupo", "codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} — {self.titulo}"


class LineaMetrado(models.Model):
    """Línea de cuantificación por caso — base para anteproyecto y costos.

    Anclaje PLN-01: ``id_pln01`` identifica el nodo/tramo del plano de inspección
    (p. ej. PB-C6, PB-V(A-B)·eje6) para vincular metrado ↔ croquis ↔ visor.
    """

    caso = models.ForeignKey(
        CasoRojo,
        on_delete=models.CASCADE,
        related_name="lineas_metrado",
        verbose_name="Caso ROJO",
    )
    orden = models.PositiveSmallIntegerField(default=1)
    partida = models.ForeignKey(
        PartidaCatalogo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineas",
        verbose_name="Partida (catálogo)",
    )
    codigo_partida = models.CharField(
        "Código partida",
        max_length=32,
        blank=True,
        help_text="Se rellena desde el catálogo; editable para Excel.",
    )
    elemento = models.CharField(
        max_length=32, choices=ch.ElementoMetrado.choices, default=ch.ElementoMetrado.PENDIENTE, blank=True
    )
    ubicacion = models.CharField(
        "Ubicación (piso / eje / torre)",
        max_length=128,
        blank=True,
        help_text="Texto libre de apoyo; preferir también id_pln01 según PLN-01.",
    )
    id_pln01 = models.CharField(
        "ID elemento PLN-01",
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Identificador del plano de inspección (p. ej. PB-C6, PB-V(A-B)·eje6, PB-M·ejeA·entre2-3).",
    )
    piso_pln = models.CharField(
        "Piso (PLN-01)",
        max_length=16,
        blank=True,
        help_text="PB, P1, P2… alineado al título del plano de ese piso.",
    )
    tipo_apuntamiento = models.CharField(
        "Tipo de apuntamiento",
        max_length=16,
        choices=ch.TipoApuntamiento.choices,
        default=ch.TipoApuntamiento.NA,
        blank=True,
        help_text="Obligatorio sentido post-sísmico cuando la partida es APUNT_*.",
    )
    cantidad = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unidad = models.CharField(
        max_length=16, choices=ch.UnidadMetrado.choices, default=ch.UnidadMetrado.PENDIENTE, blank=True
    )
    severidad = models.CharField(
        max_length=16, choices=ch.NivelABC.choices, default=ch.NivelABC.PENDIENTE, blank=True
    )
    accion = models.CharField(
        max_length=32, choices=ch.AccionMetrado.choices, default=ch.AccionMetrado.PENDIENTE, blank=True
    )
    confianza = models.CharField(
        max_length=16, choices=ch.ConfianzaMetrado.choices, default=ch.ConfianzaMetrado.PENDIENTE, blank=True
    )
    nota = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Línea de metrado"
        verbose_name_plural = "Líneas de metrado"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        ref = self.id_pln01 or self.codigo_partida or "—"
        return f"{self.caso.hab_id} · {ref} · {self.cantidad or '—'}"

    def save(self, *args, **kwargs):
        if self.partida_id:
            if not (self.codigo_partida or "").strip():
                self.codigo_partida = self.partida.codigo
            if self.unidad in ("", ch.UnidadMetrado.PENDIENTE) and self.partida.unidad_default:
                self.unidad = self.partida.unidad_default
        # Inferir piso desde id_pln01 si falta (prefijo antes del primer guion)
        if (self.id_pln01 or "").strip() and not (self.piso_pln or "").strip():
            token = self.id_pln01.strip().split("-", 1)[0].strip()
            if token:
                self.piso_pln = token[:16]
        super().save(*args, **kwargs)

    @property
    def costo_estimado(self):
        """cantidad × PU del catálogo (None si no hay precio)."""
        if self.cantidad is None or not self.partida_id or self.partida.precio_unitario is None:
            return None
        return self.cantidad * self.partida.precio_unitario


class HistorialEstado(models.Model):
    """Trazabilidad de cambios de estado en el flujo de revisión."""

    caso = models.ForeignKey(CasoRojo, on_delete=models.CASCADE, related_name="historial_estados")
    estado_anterior = models.CharField(max_length=32, blank=True)
    estado_nuevo = models.CharField(max_length=32)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    nota = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.caso.hab_id}: {self.estado_anterior} → {self.estado_nuevo}"


class HistorialDetallado(models.Model):
    """Bitácora de qué se hizo en cada guardado / acción (debajo del historial de estados)."""

    caso = models.ForeignKey(
        CasoRojo,
        on_delete=models.CASCADE,
        related_name="historial_detallado",
        verbose_name="Caso ROJO",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_detallado_casos",
    )
    resumen = models.CharField(
        "Qué se hizo (breve)",
        max_length=255,
        help_text="Nota corta del cambio (p. ej. «Actualizó dictamen y metrados»).",
    )
    detalle = models.TextField(
        "Detalle",
        blank=True,
        help_text="Campos tocados, valores anterior → nuevo, adjuntos, etc.",
    )
    origen = models.CharField(
        "Origen",
        max_length=32,
        blank=True,
        default="ficha",
        help_text="ficha · accion_estado · excel · masivo · sistema",
    )
    created_at = models.DateTimeField("Cuándo", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Historial detallado"
        verbose_name_plural = "Historial detallado"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.caso.hab_id}: {self.resumen[:60]}"


class EvidenciaFoto(models.Model):
    """Fotografía de evidencia vinculada a un caso."""

    caso = models.ForeignKey(CasoRojo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField("Imagen", upload_to="evidencias/%Y/%m/")
    descripcion = models.CharField(max_length=255, blank=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de evidencia"
        verbose_name_plural = "Fotos de evidencia"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Foto {self.pk} — caso {self.caso.hab_id}"


class CroquisAdjunto(models.Model):
    """Croquis / esquema del edificio (imagen o PDF) — sección 11 evidencia."""

    caso = models.ForeignKey(
        CasoRojo,
        on_delete=models.CASCADE,
        related_name="croquis",
        verbose_name="Caso ROJO",
    )
    archivo = models.FileField(
        "Archivo croquis",
        upload_to="croquis/%Y/%m/",
        help_text="Imagen (JPG/PNG/WEBP) o PDF del croquis / esquema estructural.",
    )
    titulo = models.CharField("Título / referencia", max_length=255, blank=True)
    codigo_piso = models.CharField(
        "Código de planta",
        max_length=16,
        blank=True,
        db_index=True,
        help_text="PB, P1, P2, SS1… — asocia el croquis a una planta del visor PLN-01.",
    )
    notas = models.TextField("Notas", blank=True)
    nombre_archivo_origen = models.CharField("Nombre archivo origen", max_length=255, blank=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="croquis_subidos",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Croquis adjunto"
        verbose_name_plural = "Croquis adjuntos"
        ordering = ["codigo_piso", "-created_at"]

    def __str__(self) -> str:
        ref = self.titulo or self.nombre_archivo_origen or f"Croquis #{self.pk}"
        piso = f"[{self.codigo_piso}] " if self.codigo_piso else ""
        return f"{self.caso.hab_id} — {piso}{ref}"


class PlantaInspeccion(models.Model):
    """Planta (nivel) del caso para el visor PLN-01 × MET-01.

    El ingeniero registra una o más plantas por edificación; en el visor
    selecciona la activa y asigna partidas a elementos (id_pln01).
    """

    caso = models.ForeignKey(
        CasoRojo,
        on_delete=models.CASCADE,
        related_name="plantas_inspeccion",
        verbose_name="Caso ROJO",
    )
    codigo_piso = models.CharField(
        "Código de planta",
        max_length=16,
        db_index=True,
        help_text="PB, P1, P2, SS1… — prefijo de los id_pln01 de esta planta.",
    )
    titulo = models.CharField(
        "Título",
        max_length=128,
        blank=True,
        help_text="Ej. Planta baja · Torre A",
    )
    orden = models.PositiveSmallIntegerField(default=1)
    croquis = models.ForeignKey(
        CroquisAdjunto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plantas",
        verbose_name="Croquis asociado",
    )
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planta de inspección"
        verbose_name_plural = "Plantas de inspección"
        ordering = ["orden", "codigo_piso", "id"]
        unique_together = [("caso", "codigo_piso")]

    def __str__(self) -> str:
        t = self.titulo or self.codigo_piso
        return f"{self.caso.hab_id} · {t}"

    def save(self, *args, **kwargs):
        self.codigo_piso = (self.codigo_piso or "").strip().upper()
        if not self.titulo:
            self.titulo = f"Planta {self.codigo_piso}"
        super().save(*args, **kwargs)
        if self.croquis_id and self.codigo_piso:
            if (self.croquis.codigo_piso or "").strip().upper() != self.codigo_piso:
                CroquisAdjunto.objects.filter(pk=self.croquis_id).update(
                    codigo_piso=self.codigo_piso
                )


class EquipoBrigada(models.Model):
    """Etiqueta legible de cada brigada (Equipo 1 — Ataguia, etc.)."""

    numero = models.PositiveSmallIntegerField(
        "N.º de equipo",
        unique=True,
        db_index=True,
        help_text="Coincide con coord.equipoN / ing.equipoN en el username.",
    )
    nombre = models.CharField(
        "Nombre / etiqueta",
        max_length=80,
        help_text="Ej. Ataguia, Ritchen, Onix.",
    )
    activo = models.BooleanField(default=True)
    notas = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Equipo / brigada"
        verbose_name_plural = "Equipos / brigadas"
        ordering = ["numero"]

    def __str__(self) -> str:
        return f"Equipo {self.numero} — {self.nombre}"

    @property
    def etiqueta(self) -> str:
        return f"Equipo {self.numero} — {self.nombre}"


class CredencialEmitida(models.Model):
    """
    Última clave en claro emitida para handoff operativo (solo visible a admin).
    Django guarda el hash; esta tabla permite recuperar la clave entregada al usuario.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credencial_emitida",
        verbose_name="Usuario",
    )
    password_plain = models.CharField("Clave emitida", max_length=128)
    emitida_en = models.DateTimeField(auto_now=True)
    emitida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credenciales_emitidas",
        verbose_name="Emitida por",
    )
    nota = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Credencial emitida"
        verbose_name_plural = "Credenciales emitidas"

    def __str__(self) -> str:
        return f"{self.user.username} · {self.emitida_en:%Y-%m-%d %H:%M}"
