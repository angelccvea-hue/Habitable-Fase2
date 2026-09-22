"""Flujo de revisión Fase II — transiciones de estado y validaciones."""
from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from inspecciones import choices as ch

GRUPO_INSPECTOR = "cpeh_inspector"
GRUPO_REVISOR = "cpeh_revisor"
GRUPO_COORDINADOR = "cpeh_coordinador"
GRUPO_CONSULTA = "cpeh_consulta"

TRANSICIONES: dict[str, set[str]] = {
    ch.Estado2daRonda.PENDIENTE: {ch.Estado2daRonda.EN_VISITA},
    ch.Estado2daRonda.EN_VISITA: {ch.Estado2daRonda.BORRADOR, ch.Estado2daRonda.PENDIENTE},
    ch.Estado2daRonda.BORRADOR: {
        ch.Estado2daRonda.PENDIENTE_REVISION,
        ch.Estado2daRonda.EN_VISITA,
    },
    ch.Estado2daRonda.PENDIENTE_REVISION: {
        ch.Estado2daRonda.REVISADO,
        ch.Estado2daRonda.APROBADO,
        ch.Estado2daRonda.BORRADOR,
    },
    ch.Estado2daRonda.REVISADO: {
        ch.Estado2daRonda.APROBADO,
        ch.Estado2daRonda.BORRADOR,
        ch.Estado2daRonda.PENDIENTE_REVISION,
    },
    ch.Estado2daRonda.APROBADO: {
        ch.Estado2daRonda.PUBLICADO,
        ch.Estado2daRonda.REVISADO,
        ch.Estado2daRonda.PENDIENTE_REVISION,
    },
    ch.Estado2daRonda.PUBLICADO: set(),
}

TRANSICIONES_POR_ROL: dict[str, set[tuple[str, str]]] = {
    # Ingeniero / inspector: campo → elevación; no aprueba ni publica.
    GRUPO_INSPECTOR: {
        (ch.Estado2daRonda.PENDIENTE, ch.Estado2daRonda.EN_VISITA),
        (ch.Estado2daRonda.EN_VISITA, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.BORRADOR, ch.Estado2daRonda.PENDIENTE_REVISION),
        (ch.Estado2daRonda.PENDIENTE_REVISION, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.REVISADO, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.EN_VISITA, ch.Estado2daRonda.PENDIENTE),
        (ch.Estado2daRonda.BORRADOR, ch.Estado2daRonda.EN_VISITA),
    },
    # Revisor técnico: cola de revisión → Revisado / Aprobado; puede devolver.
    # No publica (eso es coordinador/admin).
    GRUPO_REVISOR: {
        (ch.Estado2daRonda.PENDIENTE_REVISION, ch.Estado2daRonda.REVISADO),
        (ch.Estado2daRonda.PENDIENTE_REVISION, ch.Estado2daRonda.APROBADO),
        (ch.Estado2daRonda.PENDIENTE_REVISION, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.REVISADO, ch.Estado2daRonda.APROBADO),
        (ch.Estado2daRonda.REVISADO, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.REVISADO, ch.Estado2daRonda.PENDIENTE_REVISION),
        (ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.REVISADO),
        (ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.PENDIENTE_REVISION),
    },
    # Coordinador: opera su bolsa (como campo) + publica; NO aprueba ni marca Revisado.
    GRUPO_COORDINADOR: {
        (ch.Estado2daRonda.PENDIENTE, ch.Estado2daRonda.EN_VISITA),
        (ch.Estado2daRonda.EN_VISITA, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.BORRADOR, ch.Estado2daRonda.PENDIENTE_REVISION),
        (ch.Estado2daRonda.PENDIENTE_REVISION, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.REVISADO, ch.Estado2daRonda.BORRADOR),
        (ch.Estado2daRonda.EN_VISITA, ch.Estado2daRonda.PENDIENTE),
        (ch.Estado2daRonda.BORRADOR, ch.Estado2daRonda.EN_VISITA),
        (ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.PUBLICADO),
        # Reabrir dictamen ya aprobado (sin «aprobar» de nuevo)
        (ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.REVISADO),
        (ch.Estado2daRonda.APROBADO, ch.Estado2daRonda.PENDIENTE_REVISION),
    },
    # Consulta: sin cambios de estado
    GRUPO_CONSULTA: set(),
}


@dataclass(frozen=True)
class FlujoRevision:
    """Descripción legible del flujo operativo."""

    pasos: tuple[str, ...] = (
        "1. Pendiente verificación — caso precargado, sin visita detallada.",
        "2. En visita — inspector en campo levantando datos (secc. 4–10).",
        "3. Borrador — informe en elaboración; ingeniero puede enviar a revisión.",
        "4. Pendiente revisión — cola del revisor (informe elevado, esperando control).",
        "5. Revisado — revisor confirmó el control técnico del dictamen.",
        "6. Aprobado — dictamen validado; listo para publicar.",
        "7. Publicado — caso cerrado para tablero operativo y reportes.",
    )


def grupos_usuario(user: User) -> set[str]:
    if user.is_superuser:
        return {GRUPO_COORDINADOR, GRUPO_REVISOR, GRUPO_INSPECTOR}
    return set(user.groups.values_list("name", flat=True))


def es_coordinador(user: User) -> bool:
    return user.is_superuser or GRUPO_COORDINADOR in grupos_usuario(user)


def es_revisor(user: User) -> bool:
    return es_coordinador(user) or GRUPO_REVISOR in grupos_usuario(user)


def es_inspector(user: User) -> bool:
    return es_revisor(user) or GRUPO_INSPECTOR in grupos_usuario(user)


def puede_transicionar(user: User, anterior: str, nuevo: str) -> bool:
    if anterior == nuevo:
        return True
    # Administrador: puede fijar cualquier estado del catálogo (salta el grafo).
    if es_administrador(user):
        return nuevo in {c.value for c in ch.Estado2daRonda}
    if nuevo not in TRANSICIONES.get(anterior, set()):
        return False
    # Unión de transiciones de los grupos del usuario (coord ≠ «todo permitido»).
    g = grupos_usuario(user)
    for nombre_grupo in g:
        permitidas = TRANSICIONES_POR_ROL.get(nombre_grupo, set())
        if (anterior, nuevo) in permitidas:
            return True
    return False


def opciones_estado_2da(user: User, estado_actual: str | None) -> list[tuple[str, str]]:
    """
    Opciones del combo Estado 2da: estado actual + siguientes válidos
    según TRANSICIONES y el rol del usuario.
    Administrador: todos los estados del catálogo.
    """
    actual = (estado_actual or "").strip() or ch.Estado2daRonda.PENDIENTE
    labels = dict(ch.Estado2daRonda.choices)

    if es_administrador(user):
        out: list[tuple[str, str]] = []
        for value, label in ch.Estado2daRonda.choices:
            sufijo = " (actual)" if value == actual else ""
            out.append((value, f"{label}{sufijo}"))
        if actual not in labels:
            out.insert(0, (actual, f"{actual} (actual)"))
        return out

    permitidos: set[str] = {actual}
    for nuevo in TRANSICIONES.get(actual, set()):
        if puede_transicionar(user, actual, nuevo):
            permitidos.add(nuevo)

    out = []
    for value, label in ch.Estado2daRonda.choices:
        if value in permitidos:
            sufijo = " (actual)" if value == actual else ""
            out.append((value, f"{label}{sufijo}"))
    # Valor legado / fuera de catálogo: conservarlo para no romper el form
    if actual not in labels:
        out.insert(0, (actual, f"{actual} (actual)"))
    return out or [(actual, labels.get(actual, actual))]


def validar_transicion_estado(user: User, anterior: str, nuevo: str) -> None:
    if anterior == nuevo:
        return
    if es_administrador(user):
        if nuevo not in {c.value for c in ch.Estado2daRonda}:
            raise ValidationError(f"Estado no reconocido: «{nuevo}».")
        return
    if nuevo not in TRANSICIONES.get(anterior, set()):
        raise ValidationError(
            f"Transición no permitida: «{anterior}» → «{nuevo}». "
            f"Siguientes válidos: {', '.join(sorted(TRANSICIONES.get(anterior, set())) or ['(ninguno)'])}."
        )
    if not puede_transicionar(user, anterior, nuevo):
        raise ValidationError(
            f"Su rol no puede mover el caso de «{anterior}» a «{nuevo}». "
            "Contacte al revisor o coordinador."
        )


def validar_complementos_d(caso) -> None:
    """D1 exige complementos explícitos, plazo, medidas y detalle — cierre provisional."""
    if not ch.DecisionD.requiere_complementos(caso.decision_D):
        return

    codes = ch.parse_complementos(caso.complementos_D)
    valid = {c.value for c in ch.ComplementoD}
    invalid = [c for c in codes if c not in valid]
    if invalid:
        raise ValidationError(
            f"Códigos de complemento no válidos: {', '.join(invalid)}. "
            f"Use: {', '.join(sorted(valid))}."
        )
    if not codes:
        raise ValidationError(
            "Si la decisión es D1 (Complementos requeridos), indique al menos un código "
            "(GEO, ENS, MOD, MON, INV, REI, ALE, OTR) separados por coma."
        )
    if not caso.complemento_plazo:
        raise ValidationError(
            "D1: indique la fecha plazo / objetivo del complemento o reinspección."
        )
    if not (caso.medidas or "").strip():
        raise ValidationError(
            "D1: indique medidas inmediatas (desalojo, perímetro, prohibición de ocupación)."
        )
    detalle = (caso.complemento_detalle or "").strip()
    if len(detalle) < 15:
        raise ValidationError(
            "D1: describa qué falta, quién lo ejecuta y qué entregable cierra el complemento "
            "(mínimo 15 caracteres)."
        )
    if "OTR" in codes and len(detalle) < 40:
        raise ValidationError(
            "D1 con código OTR: amplíe el detalle del complemento (mínimo 40 caracteres)."
        )


_ESTADOS_CIERRE = (
    ch.Estado2daRonda.PENDIENTE_REVISION,
    ch.Estado2daRonda.REVISADO,
    ch.Estado2daRonda.APROBADO,
    ch.Estado2daRonda.PUBLICADO,
)

# Evidencia mínima al elevar a revisión / cerrar dictamen
MIN_FOTOS_CIERRE = 3
MIN_CROQUIS_CIERRE = 1


def validar_evidencia_cierre(caso) -> None:
    """Croquis y fotos adjuntos (archivos reales en el sistema, no solo el campo N.º fotos)."""
    n_fotos = caso.fotos.count()
    n_croquis = caso.croquis.count()
    if n_croquis < MIN_CROQUIS_CIERRE:
        raise ValidationError(
            f"Para elevar/cerrar el caso debe adjuntar al menos {MIN_CROQUIS_CIERRE} croquis "
            f"(sección evidencia / croquis). Ahora tiene {n_croquis}."
        )
    if n_fotos < MIN_FOTOS_CIERRE:
        raise ValidationError(
            f"Para elevar/cerrar el caso debe adjuntar al menos {MIN_FOTOS_CIERRE} fotografías "
            f"de evidencia. Ahora tiene {n_fotos}."
        )


def validar_fotos_informe(caso) -> None:
    """Mínimo de fotos reales para generar el PDF del sistema."""
    n_fotos = caso.fotos.count()
    if n_fotos < MIN_FOTOS_CIERRE:
        raise ValidationError(
            f"El informe PDF exige al menos {MIN_FOTOS_CIERRE} fotografías de evidencia "
            f"adjuntas en «Fotos de evidencia». Este caso tiene {n_fotos}. "
            f"Cargue las fotos faltantes y vuelva a generar el PDF."
        )


def validar_gps_visita_cierre(caso) -> None:
    """
    GPS de la visita 2 obligatorio y válido (bbox Venezuela).
    No basta el GPS Habitable de Fase I: debe haber gps_v2 parseable
    o lat/lng numéricos del control de campo.
    """
    from inspecciones.gps_utils import parse_gps

    coords = None
    if caso.lat is not None and caso.lng is not None:
        try:
            lat_f, lng_f = float(caso.lat), float(caso.lng)
            # Reusar parse_gps vía texto para aplicar el mismo bbox
            coords = parse_gps(f"{lat_f}, {lng_f}")
        except (TypeError, ValueError):
            coords = None
    if coords is None:
        coords = parse_gps(caso.gps_v2 or "")
    if coords is None:
        raise ValidationError(
            "Indique el GPS de la visita 2 (campo «GPS control (visita)») en formato "
            "lat, lng — por ejemplo 10.489497, -66.899001 — o complete latitud/longitud. "
            "El GPS de Habitable (Fase I) no sustituye el control de campo."
        )


def validar_seccion3_cierre(caso) -> None:
    """Sección 3 — validación de precarga: no puede quedar en Pendiente."""
    pendientes = []
    campos = (
        ("val_edificio", "¿Coincide el edificio?"),
        ("val_etiqueta", "¿Coincide la etiqueta ROJO?"),
        ("val_geometria", "¿Coincide la geometría?"),
        ("val_ranking", "¿Coincide el ranking/score?"),
    )
    for attr, etiqueta in campos:
        valor = getattr(caso, attr, "") or ""
        if valor in ("", ch.SiNoParcial.PENDIENTE, ch.SiNoInsuf.PENDIENTE):
            pendientes.append(etiqueta)
    if pendientes:
        raise ValidationError(
            "Complete la sección 3 (Validación) antes de elevar. Pendiente: "
            + "; ".join(pendientes)
            + "."
        )

    # Si hay discrepancia, exigir correcciones
    valores_disc = {
        caso.val_edificio,
        caso.val_etiqueta,
        caso.val_geometria,
        caso.val_ranking,
    }
    requiere_nota = bool(
        valores_disc
        & {
            ch.SiNoParcial.NO,
            ch.SiNoParcial.PARCIAL,
            ch.SiNoInsuf.NO,
            ch.SiNoInsuf.INSUF,
        }
    )
    if requiere_nota:
        tiene_estructurada = caso.correcciones_estructuradas_llenas()
        nota = (caso.correcciones or "").strip()
        if not tiene_estructurada and len(nota) < 15:
            raise ValidationError(
                "Si en la sección 3 marcó No, Parcial/corregir o Insuficiente evidencia, "
                "indique el valor correcto en los campos «… correcto» "
                "(nombre, dirección, etiqueta, pisos, GPS, score…) "
                "o escriba una nota de corrección (mínimo 15 caracteres)."
            )


def validar_inclinacion_condicional(caso) -> None:
    """Inclinación no Pendiente; si midió Δ, el valor es obligatorio."""
    incl = caso.inclinacion or ""
    if incl in ("", ch.Inclinacion.PENDIENTE):
        raise ValidationError(
            "Indique la inclinación del edificio (No / Sí cualitativa / Sí con Δ / No observable); "
            "no puede quedar en Pendiente al elevar."
        )
    if incl == ch.Inclinacion.SI_DELTA and not (caso.delta_incl or "").strip():
        raise ValidationError(
            "Si la inclinación es «Sí — con medición Δ», indique el valor de Δ (magnitud y unidad) "
            "en el campo «Δ inclinación»."
        )


def validar_dano_mecanismo_evidencia(caso) -> None:
    """Si severidad A/B/C en un elemento, exige mecanismo + evidencia (o diagnóstico mampostería)."""
    severos = {ch.NivelABC.A, ch.NivelABC.B, ch.NivelABC.C}
    pares = (
        ("col_nivel", "col_mec", "col_evidencia", "Columnas"),
        ("vig_nivel", "vig_mec", "vig_evidencia", "Vigas"),
        ("mur_nivel", "mur_mec", "mur_evidencia", "Muros/pantallas"),
        ("los_nivel", "los_mec", "los_evidencia", "Losas"),
    )
    faltan = []
    for nivel_attr, mec_attr, evid_attr, etiqueta in pares:
        nivel = getattr(caso, nivel_attr, "") or ""
        if nivel not in severos:
            continue
        if not (getattr(caso, mec_attr, "") or "").strip():
            faltan.append(f"{etiqueta}: mecanismo")
        if not (getattr(caso, evid_attr, "") or "").strip():
            faltan.append(f"{etiqueta}: ubicación/evidencia")
    mam = caso.mam_nivel or ""
    if mam in severos and not (caso.mam_diag or "").strip():
        faltan.append("Mampostería: diagnóstico")
    if faltan:
        raise ValidationError(
            "Si indicó severidad A/B/C en un elemento, complete mecanismo y evidencia "
            "(o diagnóstico en mampostería). Falta: " + "; ".join(faltan) + "."
        )


def validar_lineas_metrado_condicional(caso) -> None:
    """Acción «Otro» en una línea exige nota; líneas vacías se ignoran."""
    from inspecciones.models import LineaMetrado

    qs = LineaMetrado.objects.filter(caso=caso)
    for ln in qs:
        codigo = (ln.codigo_partida or "").strip()
        tiene_dato = bool(codigo) or (ln.cantidad is not None) or bool((ln.ubicacion or "").strip())
        if not tiene_dato:
            continue
        if ln.accion == ch.AccionMetrado.OTRO and not (ln.nota or "").strip():
            raise ValidationError(
                f"Línea de metrado orden {ln.orden}: si la acción es «Otro», "
                "indique el detalle en la nota de la línea."
            )


def validar_campos_visita_cierre(caso) -> None:
    """Datos mínimos de la visita 2 antes de enviar a revisión."""
    if not caso.fecha_v2:
        raise ValidationError(
            "Indique la fecha de la visita detallada (Fecha visita 2) antes de elevar el caso."
        )
    if not (caso.nombre_conf or "").strip():
        raise ValidationError(
            "Confirme el nombre del edificio (Nombre confirmado) antes de elevar el caso."
        )
    if not caso.inspector_asignado_id:
        raise ValidationError(
            "El caso debe tener un ingeniero/inspector asignado antes de elevarlo a revisión."
        )
    if caso.prioridad in ("", ch.PrioridadOperativa.PENDIENTE):
        raise ValidationError(
            "Indique la prioridad operativa (Inmediata, Alta o Programable); no puede quedar en Pendiente."
        )
    if not (caso.evaluadores_v2 or "").strip():
        raise ValidationError(
            "Indique los evaluadores de la visita 2 antes de elevar el caso."
        )
    if not (caso.medidas or "").strip():
        raise ValidationError(
            "Indique las medidas inmediatas (desalojo, perímetro, restricción de uso, etc.)."
        )
    validar_gps_visita_cierre(caso)
    validar_seccion3_cierre(caso)
    validar_inclinacion_condicional(caso)
    validar_dano_mecanismo_evidencia(caso)
    validar_lineas_metrado_condicional(caso)


def validar_dictamen(caso, *, cerrar: bool = False) -> None:
    """Reglas de negocio al guardar decisión / elevar a revisión."""
    exigir = cerrar or caso.estado_2da in _ESTADOS_CIERRE

    if exigir and ch.DecisionD.requiere_magnitud(caso.decision_D):
        if caso.magnitud_M in (ch.MagnitudM.PENDIENTE, ch.MagnitudM.NA, ""):
            raise ValidationError(
                "Si la decisión es D2 (Reparar / reconstruir), debe indicar magnitud M1–M4."
            )
    elif caso.decision_D and caso.decision_D != ch.DecisionD.PENDIENTE:
        if caso.magnitud_M == ch.MagnitudM.PENDIENTE:
            caso.magnitud_M = ch.MagnitudM.NA

    if exigir:
        validar_complementos_d(caso)

    if exigir:
        if caso.decision_D in ("", ch.DecisionD.PENDIENTE):
            raise ValidationError(
                "Para cerrar el informe debe registrar decisión D1–D4."
            )
        if not (caso.resumen_ejecutivo or "").strip():
            raise ValidationError(
                "Para cerrar el informe debe completar el resumen ejecutivo (secc. 11)."
            )
        validar_campos_visita_cierre(caso)
        validar_evidencia_cierre(caso)


def _ok_gps_visita(caso) -> bool:
    try:
        validar_gps_visita_cierre(caso)
        return True
    except ValidationError:
        return False


def _ok_seccion3(caso) -> bool:
    try:
        validar_seccion3_cierre(caso)
        return True
    except ValidationError:
        return False


def _ok_inclinacion(caso) -> bool:
    try:
        validar_inclinacion_condicional(caso)
        return True
    except ValidationError:
        return False


def _ok_dano_elementos(caso) -> bool:
    try:
        validar_dano_mecanismo_evidencia(caso)
        return True
    except ValidationError:
        return False


def _ok_complementos_d(caso) -> bool:
    try:
        validar_complementos_d(caso)
        return True
    except ValidationError:
        return False


def checklist_cierre(caso) -> dict:
    """
    Estado visual del cierre (sin lanzar excepciones).
    Agrupa ítems por sección del formulario (§3…§12) para ubicar lo que falta.
    Devuelve {groups, items, ok, total, listo, n_fotos, n_croquis}.
    """
    n_fotos = caso.fotos.count() if caso.pk else 0
    n_croquis = caso.croquis.count() if caso.pk else 0
    d2_mag = True
    if ch.DecisionD.requiere_magnitud(caso.decision_D):
        d2_mag = caso.magnitud_M not in (ch.MagnitudM.PENDIENTE, ch.MagnitudM.NA, "")

    def item(key: str, label: str, ok: bool, hint: str = "") -> dict:
        return {"key": key, "label": label, "ok": bool(ok), "hint": hint}

    groups_spec = [
        {
            "code": "s3",
            "title": "§3 — Validación y asignación",
            "items": [
                item(
                    "seccion3",
                    "Validación precarga completa",
                    _ok_seccion3(caso),
                    "Edificio / etiqueta / geometría / ranking",
                ),
                item(
                    "inspector",
                    "Ingeniero / inspector asignado",
                    bool(caso.inspector_asignado_id),
                    "Campo inspector en §3",
                ),
            ],
        },
        {
            "code": "s4",
            "title": "§4 — Identidad y visita 2",
            "items": [
                item("fecha_v2", "Fecha de visita 2", bool(caso.fecha_v2)),
                item(
                    "nombre_conf",
                    "Nombre del edificio confirmado",
                    bool((caso.nombre_conf or "").strip()),
                ),
                item(
                    "evaluadores",
                    "Evaluadores visita 2",
                    bool((caso.evaluadores_v2 or "").strip()),
                ),
                item(
                    "gps",
                    "GPS de la visita 2",
                    _ok_gps_visita(caso),
                    "Lat/lng o GPS control",
                ),
            ],
        },
        {
            "code": "s5",
            "title": "§5 — Daño detallado",
            "items": [
                item(
                    "inclinacion",
                    "Inclinación evaluada",
                    _ok_inclinacion(caso),
                    "No Pendiente; si midió Δ, complete el valor",
                ),
            ],
        },
        {
            "code": "s6",
            "title": "§6 — Daño por elementos",
            "items": [
                item(
                    "dano",
                    "Columnas / vigas / muros / losas",
                    _ok_dano_elementos(caso),
                    "Si A/B/C → mecanismo + evidencia",
                ),
            ],
        },
        {
            "code": "s10",
            "title": "§10 — Decisión de control",
            "items": [
                item(
                    "decision",
                    "Decisión D1–D4",
                    (caso.decision_D or "") not in ("", ch.DecisionD.PENDIENTE),
                ),
                item(
                    "magnitud",
                    "Magnitud M1–M4 (si D2)",
                    d2_mag,
                    "Obligatorio solo con D2",
                ),
                item(
                    "complementos",
                    "Complementos D1 (si aplica)",
                    _ok_complementos_d(caso),
                    "Códigos + plazo + detalle",
                ),
                item(
                    "prioridad",
                    "Prioridad operativa",
                    (caso.prioridad or "") not in ("", ch.PrioridadOperativa.PENDIENTE),
                    "Inmediata / Alta / Programable",
                ),
                item(
                    "medidas",
                    "Medidas inmediatas",
                    bool((caso.medidas or "").strip()),
                ),
            ],
        },
        {
            "code": "s11",
            "title": "§11 — Evidencia",
            "items": [
                item(
                    "fotos",
                    f"Fotos (≥{MIN_FOTOS_CIERRE})",
                    n_fotos >= MIN_FOTOS_CIERRE,
                    f"Ahora: {n_fotos} — subir en Fotos de evidencia",
                ),
                item(
                    "croquis",
                    f"Croquis (≥{MIN_CROQUIS_CIERRE})",
                    n_croquis >= MIN_CROQUIS_CIERRE,
                    f"Ahora: {n_croquis} — adjuntar en Croquis",
                ),
            ],
        },
        {
            "code": "s12",
            "title": "§12 — Resumen ejecutivo",
            "items": [
                item(
                    "resumen",
                    "Resumen ejecutivo",
                    bool((caso.resumen_ejecutivo or "").strip()),
                    "Párrafo de cierre para revisión",
                ),
            ],
        },
    ]

    groups = []
    flat: list[dict] = []
    for g in groups_spec:
        # Pendientes primero dentro de cada sección
        ordered = sorted(g["items"], key=lambda it: (it["ok"], it["label"]))
        ok_g = sum(1 for it in ordered if it["ok"])
        groups.append(
            {
                "code": g["code"],
                "title": g["title"],
                "ok": ok_g,
                "total": len(ordered),
                "listo": ok_g == len(ordered),
                "items": ordered,
            }
        )
        flat.extend(ordered)

    ok_n = sum(1 for it in flat if it["ok"])
    return {
        "groups": groups,
        "items": flat,
        "ok": ok_n,
        "total": len(flat),
        "listo": ok_n == len(flat),
        "n_fotos": n_fotos,
        "n_croquis": n_croquis,
    }


def asegurar_grupos() -> dict[str, Group]:
    grupos = {}
    for nombre in (GRUPO_INSPECTOR, GRUPO_REVISOR, GRUPO_COORDINADOR, GRUPO_CONSULTA):
        grupos[nombre], _ = Group.objects.get_or_create(name=nombre)
    return grupos


def es_administrador(user: User) -> bool:
    """Superusuario del sistema (gestión global y asignación en cascada)."""
    return bool(user.is_authenticated and user.is_superuser)


def es_solo_inspector(user: User) -> bool:
    """Inspector de campo: no es coordinador ni revisor ni admin."""
    if not user.is_authenticated or user.is_superuser:
        return False
    g = grupos_usuario(user)
    return (
        GRUPO_INSPECTOR in g
        and GRUPO_REVISOR not in g
        and GRUPO_COORDINADOR not in g
        and GRUPO_CONSULTA not in g
    )


def es_solo_revisor(user: User) -> bool:
    """Revisor técnico: no es coordinador ni admin."""
    if not user.is_authenticated or user.is_superuser:
        return False
    g = grupos_usuario(user)
    return GRUPO_REVISOR in g and GRUPO_COORDINADOR not in g and GRUPO_CONSULTA not in g


def es_solo_coordinador(user: User) -> bool:
    """Coordinador operativo (no admin)."""
    if not user.is_authenticated or user.is_superuser:
        return False
    return GRUPO_COORDINADOR in grupos_usuario(user)


def es_solo_consulta(user: User) -> bool:
    """Solo lectura: ve inventario, no edita ni asigna."""
    if not user.is_authenticated or user.is_superuser:
        return False
    g = grupos_usuario(user)
    return GRUPO_CONSULTA in g and GRUPO_COORDINADOR not in g and GRUPO_REVISOR not in g


def puede_asignar_casos(user: User) -> bool:
    """Admin y coordinadores asignan; revisores, consulta e ingenieros no."""
    if not user.is_authenticated or es_solo_consulta(user):
        return False
    return bool(user.is_superuser or GRUPO_COORDINADOR in grupos_usuario(user))


def puede_modificar_casos(user: User) -> bool:
    """False para rol consulta (solo ver / exportar)."""
    if not user.is_authenticated:
        return False
    if es_solo_consulta(user):
        return False
    return True


def ve_todos_los_casos(user: User) -> bool:
    """Inventario completo: admin, revisor o consulta (solo lectura)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return es_solo_revisor(user) or es_solo_consulta(user)


def filtrar_casos_por_rol(user: User, qs=None):
    """
    Alcance de casos:
    - Administrador: todos
    - Revisor (solo): todos (puede ver; no asigna)
    - Consulta: todos (solo lectura)
    - Coordinador: solo coordinador_asignado = user
    - Inspector: solo inspector_asignado = user
    - Staff sin rol: ninguno
    """
    from inspecciones.models import CasoRojo

    if qs is None:
        qs = CasoRojo.objects.all()
    if not user.is_authenticated:
        return qs.none()
    if user.is_superuser or es_solo_revisor(user) or es_solo_consulta(user):
        return qs
    g = grupos_usuario(user)
    if GRUPO_COORDINADOR in g:
        return qs.filter(coordinador_asignado=user)
    if GRUPO_INSPECTOR in g:
        return qs.filter(inspector_asignado=user)
    return qs.none()


def usuario_puede_ver_caso(user: User, caso) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or es_solo_revisor(user) or es_solo_consulta(user):
        return True
    if caso.coordinador_asignado_id == user.id:
        return True
    if caso.inspector_asignado_id == user.id:
        return True
    if caso.revisor_asignado_id == user.id:
        return True
    return False
