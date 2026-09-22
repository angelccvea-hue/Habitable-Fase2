"""Secciones numeradas del informe — títulos + guías wizard (admin + PDF).

Las «description» de cada fieldset se muestran arriba de los campos en el admin
(Jazzmin/Django con |safe). El PDF/Excel solo usan títulos y campos de
``CASE_FIELDSETS`` (sin el campo de formulario ``procedimientos_catalogo``).
"""
from __future__ import annotations

from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe


def _wizard(
    paso: str,
    *,
    objetivo: str,
    que_hacer: str,
    clasificaciones: str | None = None,
    ejemplo: str | None = None,
    no_hacer: str | None = None,
    catalogo_html: str | SafeString | None = None,
) -> SafeString:
    """Bloque didáctico reutilizable para cada sección del formulario."""
    partes = [
        format_html(
            '<div class="cpeh-wizard">'
            '<div class="cpeh-wizard-paso">Paso {}</div>'
            '<p class="cpeh-wizard-obj"><strong>Objetivo:</strong> {}</p>'
            '<p class="cpeh-wizard-do"><strong>Qué rellenar:</strong> {}</p>',
            paso,
            mark_safe(objetivo),
            mark_safe(que_hacer),
        )
    ]
    if clasificaciones:
        partes.append(
            format_html(
                '<div class="cpeh-wizard-box">'
                "<strong>Clasificaciones:</strong> {}"
                "</div>",
                mark_safe(clasificaciones),
            )
        )
    if catalogo_html:
        partes.append(format_html("{}", catalogo_html))
    if ejemplo:
        partes.append(
            format_html(
                '<div class="cpeh-wizard-ej">'
                "<strong>Ejemplo de llenado:</strong> {}"
                "</div>",
                mark_safe(ejemplo),
            )
        )
    if no_hacer:
        partes.append(
            format_html(
                '<p class="cpeh-wizard-no"><strong>Importante:</strong> {}</p>',
                mark_safe(no_hacer),
            )
        )
    partes.append(mark_safe("</div>"))
    return mark_safe("".join(str(p) for p in partes))


def _html_catalogo_procedimientos(*, limite: int | None = None) -> SafeString:
    """Lista HTML del catálogo VIG/COL/MAM para el wizard de la sección 8."""
    from inspecciones.catalogo_procedimientos import listar_procedimientos_ayuda

    rows = listar_procedimientos_ayuda(limite=limite)
    if not rows:
        return mark_safe(
            '<div class="cpeh-wizard-cat">'
            '<p class="cpeh-wizard-cat-vacio">Catálogo de procedimientos no disponible.</p>'
            "</div>"
        )
    items = format_html_join(
        "",
        (
            '<li class="cpeh-wizard-cat-item">'
            '<code class="cpeh-wizard-cat-code">{}</code>'
            " — {} "
            '<span class="cpeh-wizard-cat-meta">({})</span>'
            "</li>"
        ),
        ((r["codigo"], r["titulo"], r["categoria"]) for r in rows),
    )
    return format_html(
        '<div class="cpeh-wizard-cat">'
        '<div class="cpeh-wizard-cat-titulo">Catálogo de procedimientos (códigos vigentes)</div>'
        '<ul class="cpeh-wizard-cat-lista">{}</ul>'
        "</div>",
        items,
    )


def _html_catalogo_partidas(*, limite: int | None = None) -> SafeString:
    """Lista HTML del catálogo de partidas para el wizard de la sección 9."""
    from inspecciones.partidas_catalogo import listar_partidas_ayuda

    rows = listar_partidas_ayuda(limite=limite)
    if not rows:
        return mark_safe(
            '<div class="cpeh-wizard-cat">'
            '<p class="cpeh-wizard-cat-vacio">Catálogo de partidas no disponible.</p>'
            "</div>"
        )
    items = format_html_join(
        "",
        (
            '<li class="cpeh-wizard-cat-item">'
            '<code class="cpeh-wizard-cat-code">{}</code>'
            " — {} "
            '<span class="cpeh-wizard-cat-meta">[{} · {}]</span>'
            "</li>"
        ),
        ((r["codigo"], r["titulo"], r["grupo"], r["unidad"]) for r in rows),
    )
    return format_html(
        '<div class="cpeh-wizard-cat">'
        '<div class="cpeh-wizard-cat-titulo">Catálogo de partidas / metrados (códigos vigentes)</div>'
        '<ul class="cpeh-wizard-cat-lista">{}</ul>'
        "</div>",
        items,
    )


def _fieldset_core(
    *,
    include_procedimientos_catalogo: bool = False,
) -> tuple[tuple[str, dict], ...]:
    """Fieldsets con descripciones wizard; §8/§9 incluyen catálogo en vivo."""
    fields_s8: tuple[str, ...]
    if include_procedimientos_catalogo:
        fields_s8 = (
            "procedimientos_catalogo",
            "proc_codigos",
            "repar_viable",
            "proc_notas",
        )
    else:
        fields_s8 = ("proc_codigos", "repar_viable", "proc_notas")

    return (
        (
            "1 — Precarga Habitable (Fase 1)",
            {
                "description": _wizard(
                    "1 de 12",
                    objetivo=(
                        "Revisar los datos traídos de Habitable / Fase 1. "
                        "Es la «foto» inicial del caso; sirve de referencia."
                    ),
                    que_hacer=(
                        "Solo <em>lea</em> y verifique. Estos campos están "
                        "<strong>bloqueados</strong> (precarga Habitable). "
                        "Si hay error, use la <strong>sección 3</strong> "
                        "(Sí/No/Parcial + campos «… correcto»)."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Etiqueta Fase 1</strong> — normalmente ROJO "
                        "(esta fase solo trata ROJO).</li>"
                        "<li><strong>GPS Habitable</strong> — punto de la inspección rápida; "
                        "puede diferir del GPS de visita 2.</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "ID 290813 · Edificio «Los Robles» · ROJO · 8 pisos / 1 sótano · "
                        "GPS Habitable 10.60, −66.93 · Observaciones: «grietas en PB»."
                    ),
                    no_hacer=(
                        "No borre ni vacíe esta sección «para empezar de cero». "
                        "La precarga se conserva; lo de visita se llena desde la sección 3 en adelante."
                    ),
                ),
                "fields": (
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
                ),
            },
        ),
        (
            "2 — Ranking y prioridad",
            {
                "description": _wizard(
                    "2 de 12",
                    objetivo=(
                        "Entender <em>por qué</em> este caso quedó con ese score/banda: "
                        "es la urgencia relativa del ranking operativo (cola de verificación "
                        "detallada). Orientación de trabajo, <strong>no</strong> dictamen "
                        "de demolición."
                    ),
                    que_hacer=(
                        "Solo <em>lea</em>. Score, banda, puestos, detalle y probabilidad "
                        "relativa están <strong>bloqueados</strong> (también para admin). "
                        "Si en campo el ranking no cuadra, márquelo en la "
                        "<strong>sección 3</strong> (<code>val_ranking</code> + "
                        "<code>corr_score</code> / <code>corr_banda</code>); al guardar "
                        "se actualiza la precarga."
                    ),
                    clasificaciones=(
                        "<p><strong>Cómo se lee el score (0–100)</strong> — suma de "
                        "señales ya capturadas en la planilla Habitable (Fase 1). "
                        "Mayor = más urgente en la cola. Vacío en un ítem = no suma "
                        "(un ROJO poco llenado puede quedar con score bajo).</p>"
                        "<p><strong>Bandas según el número</strong> "
                        "(no confundir con la prioridad operativa Inmediata/Alta/"
                        "Programable de la sección 10):</p>"
                        '<table class="cpeh-wizard-table">'
                        "<thead><tr><th>Score</th><th>Banda</th><th>Qué implica</th></tr></thead>"
                        "<tbody>"
                        "<tr><td>80–100</td><td><strong>Muy alta</strong></td>"
                        "<td>Varias señales graves a la vez; máxima prioridad de "
                        "verificación; fuerte probabilidad relativa de que el dictamen "
                        "posterior oriente a demolición.</td></tr>"
                        "<tr><td>60–79</td><td><strong>Alta</strong></td>"
                        "<td>Priorizar en la cola de segunda ronda (primera ola operativa "
                        "suele filtrar score ≥ 60).</td></tr>"
                        "<tr><td>40–59</td><td><strong>Media</strong></td>"
                        "<td>Verificar; puede ser ROJO por riesgo importante, no "
                        "necesariamente demolición inmediata.</td></tr>"
                        "<tr><td>20–39</td><td><strong>Baja-media</strong></td>"
                        "<td>Menor señal acumulada en Fase 1; no excluir sin revisión "
                        "(a veces falta llenado).</td></tr>"
                        "<tr><td>0–19</td><td><strong>Baja / datos incompletos</strong></td>"
                        "<td>Pocos campos de gravedad en C, o edificio alto con poca "
                        "señal estructural en planilla. Tratar como «curar dato», no "
                        "como «edificio sano».</td></tr>"
                        "</tbody></table>"
                        "<p><strong>De dónde salen los puntos</strong> "
                        "(A = poco/nulo · B = medio · C = máximo del ítem). "
                        "El campo <em>Detalle del score</em> lista exactamente qué sumó "
                        "(ej. <code>riesgo_externo+20; ext_colapso+15; altura_10++6</code>):</p>"
                        "<ul>"
                        "<li><strong>riesgo_externo</strong> — B +8 · C +20</li>"
                        "<li><strong>riesgo_severo</strong> — B +8 · C +20</li>"
                        "<li><strong>ext_colapso_estructura</strong> — B +6 · C +15</li>"
                        "<li><strong>ext_peligro_aledanos</strong> — B +4 · C +10</li>"
                        "<li><strong>ext_inclinacion</strong> — B +3 · C +8</li>"
                        "<li><strong>ext_asentamiento / peligro_geologico</strong> — B +2 · C +5 c/u</li>"
                        "<li><strong>acc_medidas</strong> — DEMOLER +8 · apuntalar+acordonar +4 · una sola +2</li>"
                        "<li><strong>emergencia_gas</strong> — sí +3</li>"
                        "<li><strong>Altura (pisos)</strong> — 1–2 +1 · 3–5 +3 · 6–9 +5 · 10+ +6</li>"
                        "<li><strong>piso_critico</strong> informado — +3 · conteos sev_* — hasta +5</li>"
                        "</ul>"
                        "<p><strong>Puestos</strong> — orden relativo (p. ej. La Guaira / "
                        "nacional) tras ordenar por score. "
                        "<strong>Probabilidad relativa</strong> — texto asociado a la banda.</p>"
                    ),
                    ejemplo=(
                        "Score 78 · Banda Alta · Puesto 12 La Guaira / 145 nacional · "
                        "Detalle: <code>riesgo_externo+20; ext_colapso+15; "
                        "acc_demoler+8; altura_10++6; …</code> → se entiende por qué "
                        "queda en Alta (60–79) y no en Muy alta (≥80)."
                    ),
                    no_hacer=(
                        "No edite score/banda aquí ni los borre «para empezar de cero». "
                        "El ranking <em>no</em> elige solo D1–D4: la decisión de control "
                        "se registra en la sección 10 tras la visita."
                    ),
                ),
                "fields": ("score", "banda", "puestos", "score_detalle", "prob_rel"),
            },
        ),

        (
            "3 — Validación de la precarga",
            {
                "description": _wizard(
                    "3 de 12",
                    objetivo=(
                        "Confirmar en campo si la precarga (edificio, etiqueta, geometría, ranking) "
                        "es correcta. Aquí se corrige la «ficha de fábrica»."
                    ),
                    que_hacer=(
                        "Para cada ítem marque <strong>Sí / No / Parcial</strong> "
                        "(o Insuficiente en etiqueta). "
                        "Si marca No o Parcial, complete el campo «… correcto»: al guardar se "
                        "actualiza la precarga (secc. 1–2) y el Excel. Asigne coordinador / "
                        "ingeniero / revisor si corresponde."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Sí</strong> — coincide con lo visitado.</li>"
                        "<li><strong>No</strong> — error claro; indique el valor correcto.</li>"
                        "<li><strong>Parcial / corregir</strong> — hay matices; corrija y explique.</li>"
                        "<li><strong>Insuficiente evidencia</strong> (etiqueta) — no puede confirmar aún.</li>"
                        "<li><strong>Pendiente</strong> — aún no validó; no puede quedar así al elevar "
                        "a revisión.</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "val_edificio = No → Nombre correcto: «Edif. Los Robles Torre B». "
                        "val_geometria = Parcial → Pisos correctos: «10 / 2». "
                        "val_ranking = Sí."
                    ),
                    no_hacer=(
                        "No deje todo en Pendiente si ya visitó. Sin validación completa el sistema "
                        "bloquea el envío a Revisado."
                    ),
                ),
                "fields": (
                    "val_edificio",
                    "corr_nombre",
                    "corr_direccion",
                    "corr_muni_parr",
                    "val_etiqueta",
                    "corr_etiqueta",
                    "val_geometria",
                    "corr_pisos",
                    "corr_gps",
                    "val_ranking",
                    "corr_score",
                    "corr_banda",
                    "correcciones",
                    "coordinador_asignado",
                    "inspector_asignado",
                    "revisor_asignado",
                ),
            },
        ),
        (
            "4 — Identidad y edificio (visita 2)",
            {
                "description": _wizard(
                    "4 de 12",
                    objetivo=(
                        "Registrar la identidad confirmada del inmueble en la visita detallada "
                        "(no la precarga de Fase 1)."
                    ),
                    que_hacer=(
                        "Complete nombre confirmado, fecha de visita, "
                        "<strong>GPS de control (visita)</strong>, "
                        "evaluadores, supervisor, uso, pisos/sótanos confirmados, sistema estructural, "
                        "ocupación y peligro a aledaños."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Sistema</strong> — pórtico, muros, mixto, etc. "
                        "(lista del sistema).</li>"
                        "<li><strong>Ocupación</strong> — habitado / deshabitado / parcial / "
                        "no observable.</li>"
                        "<li><strong>Peligro aledaños</strong> — Sí / No / No observable.</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "Nombre conf.: Los Robles T-B · Fecha 10/09/2026 · "
                        "GPS visita: 10.6012, −66.9310 · Evaluadores: Ing. Pérez; Ing. Díaz · "
                        "Uso: Mixto · Pisos 10 / sótanos 2 · Sistema: Pórtico RC · "
                        "Ocupación: Parcial · Peligro aledaños: Sí."
                    ),
                    no_hacer=(
                        "El GPS de visita 2 es obligatorio al elevar. "
                        "No basta el GPS Habitable de la secc. 1."
                    ),
                ),
                "fields": (
                    "nombre_conf",
                    "fecha_v2",
                    "gps_v2",
                    "evaluadores_v2",
                    "supervisor_v2",
                    "uso",
                    "pisos_conf",
                    "sotanos_conf",
                    "sistema",
                    "ocupacion",
                    "peligro_aledanos",
                ),
            },
        ),
        (
            "5 — Daño detallado (visita 2)",
            {
                "description": _wizard(
                    "5 de 12",
                    objetivo=(
                        "Síntesis del daño global observado: piso crítico, columnas, inclinación, "
                        "vigas, losas, fachada y análisis del ingeniero."
                    ),
                    que_hacer=(
                        "Indique piso crítico, % de columnas afectadas e inclinación "
                        "(obligatoria al elevar; no deje Pendiente). "
                        "Si midió Δ, complete «Δ inclinación» (obligatorio). "
                        "Nivele daño en vigas, losas y riesgo de fachada (A/B/C). "
                        "Si las losas están comprometidas en varios pisos, márquelo aquí "
                        "y detalle mecanismo/evidencia en la sección 6. "
                        "Cierre con un análisis libre breve."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Nivel A / B / C</strong> (vigas, losas, fachada) — "
                        "A leve · B moderado · C severo (o «No observable» / Pendiente).</li>"
                        "<li><strong>% columnas</strong> — tramos "
                        "(&lt;10%, 10–30%, &gt;30%, &gt;50%, etc.).</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "Piso crítico: PB–1 · Columnas &gt;30% · Inclinación: aparente hacia calle · "
                        "Δ: 1.2° (inclinómetro) · Vigas: B · Losas: B (entrepisos 3–5) · Fachada: C · "
                        "Análisis: «pérdida de capacidad en PB; losas fisuradas en varios niveles»."
                    ),
                    no_hacer=(
                        "No deje «Pendiente» en inclinación ni en los niveles si ya pudo observar. "
                        "Si inclinación = con medición Δ, no omita el valor Δ. "
                        "El detalle por elemento (columnas/vigas/muros/losas) va en la sección 6."
                    ),
                ),
                "fields": (
                    "piso_crit_v2",
                    "pct_columnas",
                    "inclinacion",
                    "delta_incl",
                    "dano_vigas",
                    "dano_losas",
                    "riesgo_fachada",
                    "analisis_libre",
                ),
            },
        ),
        (
            "6 — Daño estructural (detalle: columnas, vigas, muros, losas)",
            {
                "description": _wizard(
                    "6 de 12",
                    objetivo=(
                        "Documentar el daño por elemento estructural "
                        "(columnas, vigas, muros/pantallas y <strong>losas</strong>) "
                        "con mecanismo, nivel y evidencia localizable."
                    ),
                    que_hacer=(
                        "Por cada elemento — incluidas las <strong>losas</strong> —: "
                        "mecanismo de falla, nivel A/B/C, y ubicación/evidencia "
                        "(piso, eje, zona). Si marca A/B/C, mecanismo y evidencia son obligatorios al elevar. "
                        "Si el daño en losas abarca varios niveles, descríbalo aquí (no solo en el resumen). "
                        "Complete escaleras/evacuación y daños preexistentes (pre 24/06/2026)."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>A</strong> — daño leve / reparable local.</li>"
                        "<li><strong>B</strong> — daño moderado; requiere intervención planificada.</li>"
                        "<li><strong>C</strong> — daño severo; compromete estabilidad o seguridad.</li>"
                        "<li><strong>No observable</strong> — no pudo inspeccionar "
                        "(acceso, recubrimiento, etc.).</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "Columnas: aplastamiento núcleo · Nivel C · Evidencia: "
                        "«ejes A–C, PB, FOTOS 4–7». "
                        "Losas: fisuras diagonales · Nivel B · Evidencia: "
                        "«entrepiso 3–5 zona central». "
                        "Preexistentes: «humedad crónica losa azotea (no sísmico)»."
                    ),
                    no_hacer=(
                        "No omita el bloque Losas si vio daño en entrepisos o azotea. "
                        "No deje solo el comentario en el resumen (§5 / conclusión)."
                    ),
                ),
                "fields": (
                    "col_mec",
                    "col_nivel",
                    "col_evidencia",
                    "vig_mec",
                    "vig_nivel",
                    "vig_evidencia",
                    "mur_mec",
                    "mur_nivel",
                    "mur_evidencia",
                    "los_mec",
                    "los_nivel",
                    "los_evidencia",
                    "escaleras",
                    "preexistentes",
                ),
            },
        ),
        (
            "7 — Mampostería",
            {
                "description": _wizard(
                    "7 de 12",
                    objetivo=(
                        "Registrar daño en muros no estructurales / de arriostre que puedan afectar "
                        "seguridad (caída a vía, ocupación, etc.)."
                    ),
                    que_hacer=(
                        "Indique mecanismo, nivel A/B/C y diagnóstico "
                        "(fisuras, pandeo, desprendimiento…)."
                    ),
                    clasificaciones=(
                        "Misma escala <strong>A / B / C / No observable / Pendiente</strong> "
                        "que en daño estructural."
                    ),
                    ejemplo=(
                        "Mecanismo: desprendimiento de paños · Nivel C · "
                        "Diagnóstico: «fachada norte PB–2, riesgo a acera; "
                        "apuntalar / desalojar zona»."
                    ),
                ),
                "fields": ("mam_mec", "mam_nivel", "mam_diag"),
            },
        ),
        (
            "8 — Procedimientos sugeridos",
            {
                "description": _wizard(
                    "8 de 12",
                    objetivo=(
                        "Proponer procedimientos técnicos de reparación según el catálogo "
                        "oficial VIG / COL / MAM (inyección, recubrimiento, reconstrucción, "
                        "encamisado, etc.)."
                    ),
                    que_hacer=(
                        "Marque en el catálogo los códigos aplicables (o escríbalos en "
                        "<strong>proc_codigos</strong> separados por coma). Indique si la "
                        "reparación es viable con la información actual y agregue notas "
                        "operativas (secuencia, shoring, supuestos)."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Reparación viable</strong> — Sí / No / Insuficiente evidencia "
                        "/ Pendiente.</li>"
                        "<li><strong>Códigos</strong> — use los del catálogo debajo "
                        "(p. ej. COL-04, COL-05, MAM-03).</li>"
                        "</ul>"
                    ),
                    catalogo_html=_html_catalogo_procedimientos(),
                    ejemplo=(
                        "Códigos: <code>COL-04</code>, <code>COL-05</code>, <code>MAM-03</code> · "
                        "Reparación viable: Insuficiente evidencia · "
                        "Notas: «reconstruir PB ejes A–C bajo descarga; encamisar laterales; "
                        "llaveado fachada norte; requiere GEO + acceso a sótano antes de D2»."
                    ),
                    no_hacer=(
                        "No invente códigos fuera del catálogo salvo nota explícita. "
                        "Las <strong>cantidades por partida</strong> van en la sección 9 "
                        "y en la tabla ancha «Líneas de metrado» (como Excel Metrados)."
                    ),
                ),
                "classes": ("cpeh-proc-wide",),
                "fields": fields_s8,
            },
        ),
        (
            "9 — Cuantificación para intervención (metrados)",
            {
                "classes": ("cpeh-metrado-wide",),
                "description": _wizard(
                    "9 de 12",
                    objetivo=(
                        "Cuantificar la intervención como en Excel «Metrados»: "
                        "totales del edificio + <strong>una fila por partida con cantidad</strong>."
                    ),
                    que_hacer=(
                        "1) Complete totales arriba. "
                        "2) En la tabla <strong>Líneas de metrado</strong> (planilla naranja, "
                        "abajo o pestaña homónima) agregue renglones: partida/código, ubicación, "
                        "<strong>cantidad</strong> (columna amarilla), unidad, severidad, acción. "
                        "3) O cargue el Excel (hoja Metrados) desde Herramientas."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Cantidad</strong> — número por renglón (equivale a columna F del Excel).</li>"
                        "<li><strong>Confianza del metrado</strong> — Alta / Media / Estimada (global).</li>"
                        "<li><strong>Agregar otra línea</strong> — más filas vacías, como en Excel.</li>"
                        "</ul>"
                    ),
                    catalogo_html=_html_catalogo_partidas(),
                    ejemplo=(
                        "Área 2 400 m² · 32 viviendas · Escombros 180 m³ · Niveles 1–4 · "
                        "Líneas: <code>APUNT_COL</code> · Columna · PB eje B · <strong>8 und</strong> · "
                        "<code>REP_COL_LOCAL</code> · <strong>12 und</strong> · Severidad C · Acción Reparar."
                    ),
                    no_hacer=(
                        "Las notas de cuantificación no sustituyen las líneas de metrado. "
                        "Si no hay líneas con cantidad, el anteproyecto queda incompleto."
                    ),
                ),
                "fields": (
                    "area_aprox_m2",
                    "n_viviendas",
                    "vol_escombros_m3",
                    "m_fachada_riesgo",
                    "niveles_intervenir",
                    "pct_estructura_intervenir",
                    "metrado_confianza",
                    "metrado_notas",
                ),
            },
        ),
        (
            "10 — Decisión de control",
            {
                "description": _wizard(
                    "10 de 12",
                    objetivo=(
                        "Registrar el dictamen de Fase II: estado del flujo, decisión D1–D4, "
                        "magnitud (si D2), prioridad operativa y medidas."
                    ),
                    que_hacer=(
                        "<strong>No es automático.</strong> Mientras no haya dictamen, D / M / "
                        "prioridad quedan en <em>Pendiente</em> (correcto al inicio). Tras la "
                        "visita, el ingeniero elige D1–D4. Al enviar a <strong>Revisado</strong> "
                        "el sistema exige que ya no estén en Pendiente."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Estado 2.ª ronda</strong> — Pendiente verificación → En visita → "
                        "Borrador → Revisado → Aprobado → Publicado (flujo de trabajo).</li>"
                        "<li><strong>D1</strong> — Complementos requeridos "
                        "(estudios / reinspección). Complete códigos GEO, ENS, MOD…</li>"
                        "<li><strong>D2</strong> — Reparar / reconstruir "
                        "(+ <strong>magnitud M1–M4</strong> obligatoria).</li>"
                        "<li><strong>D3</strong> — Demoler · <strong>D4</strong> — "
                        "Escombros / ya colapsado.</li>"
                        "<li><strong>Prioridad operativa</strong> — Inmediata / Alta / Programable "
                        "(distinta de la banda del ranking secc. 2).</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "Estado: Borrador → luego Revisado · Decisión: D2 Reparar · Magnitud: M2 · "
                        "Prioridad: Alta · Medidas: «desalojo PB–1; apuntalar; perímetro 10 m» · "
                        "Justificación: «capacidad residual insuficiente en PB; viable reforzar»."
                    ),
                    no_hacer=(
                        "«Pendiente» en D/M/prioridad al inicio es normal. "
                        "No deje Pendiente al elevar. Por regla se privilegia D2; D3/D4 solo con "
                        "justificación fuerte. Si no es D2, la magnitud puede quedar N/A."
                    ),
                ),
                "fields": (
                    "estado_2da",
                    "decision_D",
                    "complementos_D",
                    "complemento_plazo",
                    "complemento_detalle",
                    "magnitud_M",
                    "prioridad",
                    "medidas",
                    "justificacion",
                ),
            },
        ),
        (
            "11 — Evidencia, croquis y firmas",
            {
                "description": _wizard(
                    "11 de 12",
                    objetivo=(
                        "Dejar evidencia verificable: fotos, croquis e identificación de firmas."
                    ),
                    que_hacer=(
                        "Adjunte <strong>al menos 3 fotografías</strong> en «Fotos de evidencia» "
                        "(archivos reales) y al menos 1 croquis en «Croquis adjuntos». Indique "
                        "firmas (elaboró / revisó / aprobó). "
                        "El campo N.º de fotos se alinea al cerrar; lo que cuenta son los archivos."
                    ),
                    clasificaciones=(
                        "<ul>"
                        "<li><strong>Fotos</strong> — mínimo 3 para generar el PDF del sistema "
                        "y para elevar a revisión.</li>"
                        "<li><strong>Croquis</strong> — imagen o PDF; mínimo 1 al elevar.</li>"
                        "<li><strong>PDF de campo</strong> — opcional; se fusiona como anexo "
                        "al PDF generado.</li>"
                        "</ul>"
                    ),
                    ejemplo=(
                        "3+ fotos: fachada, PB columnas, piso crítico · "
                        "Croquis: planta PB anotada · "
                        "Firmas: Elaboró Ing. Pérez / Revisó Ing. Gómez."
                    ),
                    no_hacer=(
                        "Sin 3 fotos el botón de PDF queda bloqueado y el sistema no deja "
                        "elevar el caso."
                    ),
                ),
                "fields": ("n_fotos", "firmas"),
            },
        ),
        (
            "12 — Resumen ejecutivo",
            {
                "description": _wizard(
                    "12 de 12",
                    objetivo=(
                        "Cerrar con un párrafo comprensible para revisión, coordinación "
                        "y mesas de trabajo."
                    ),
                    que_hacer=(
                        "Redacte situación del edificio, decisión recomendada (D/M), urgencia "
                        "y próximos pasos. Debe entenderse sin leer todo el detalle técnico. "
                        "Obligatorio al elevar/cerrar."
                    ),
                    ejemplo=(
                        "«Edificio mixto 10 pisos en La Guaira con daño severo en PB (columnas C). "
                        "Se recomienda D2-M2 con prioridad Alta: desalojo parcial, apuntalamiento y "
                        "diseño de refuerzo. Complementar con GEO si se confirma soterramiento.»"
                    ),
                    no_hacer=(
                        "No deje vacío al enviar a Revisado. Evite solo copiar listas de campos "
                        "sin síntesis."
                    ),
                ),
                "fields": ("resumen_ejecutivo",),
            },
        ),
        (
            "13 — Auditoría del sistema",
            {
                "classes": ("collapse",),
                "description": _wizard(
                    "Auditoría",
                    objetivo="Metadatos internos del sistema (no forman parte del dictamen técnico).",
                    que_hacer="Solo consulta: fechas de creación y última actualización del registro.",
                    no_hacer="No requiere llenado por el equipo de campo.",
                ),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


def get_case_fieldsets() -> tuple[tuple[str, dict], ...]:
    """Fieldsets para Excel/PDF/export: §8 sin ``procedimientos_catalogo``."""
    return _fieldset_core(include_procedimientos_catalogo=False)


def get_case_fieldsets_admin() -> tuple[tuple[str, dict], ...]:
    """Fieldsets para el admin: §8 incluye el campo de formulario ``procedimientos_catalogo``."""
    return _fieldset_core(include_procedimientos_catalogo=True)


# Export estático usado por excel_plantilla / report_sections (solo campos del modelo).
CASE_FIELDSETS: tuple[tuple[str, dict], ...] = get_case_fieldsets()
