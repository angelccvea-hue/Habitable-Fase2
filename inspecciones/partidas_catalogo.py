"""Catálogo semilla de partidas para metrados / futuros costos."""
from __future__ import annotations

from inspecciones import choices as ch

# codigo, grupo, titulo, unidad, aplica_decisiones, orden, descripcion
PARTIDAS_SEMILLA: list[tuple] = [
    # —— Apuntamiento post-sísmico (preventivo vs de trabajo) ——
    (
        "APUNT_PREV",
        ch.GrupoPartida.APUNT,
        "Apuntalamiento preventivo post-sísmico (estabilización)",
        ch.UnidadMetrado.PISO,
        "D2,D3",
        8,
        "Estabilizar edificio dañado ante gravedad y réplicas; no sustituye plan calculado",
    ),
    (
        "APUNT_PISO",
        ch.GrupoPartida.APUNT,
        "Apuntalamiento de trabajo por piso",
        ch.UnidadMetrado.PISO,
        "D2,D3",
        10,
        "Shoring temporal por nivel durante la intervención",
    ),
    (
        "APUNT_COL",
        ch.GrupoPartida.APUNT,
        "Apuntalamiento de trabajo — columnas",
        ch.UnidadMetrado.UND,
        "D2,D3",
        11,
        "Und = columna; anclar a ID PLN-01 (p. ej. PB-C6)",
    ),
    (
        "APUNT_VIGA",
        ch.GrupoPartida.APUNT,
        "Apuntalamiento de trabajo — vigas / losas tributarias",
        ch.UnidadMetrado.UND,
        "D2,D3",
        12,
        "Und = tramo; anclar a ID PLN-01 de viga",
    ),
    (
        "ACORD_PERIM",
        ch.GrupoPartida.APUNT,
        "Acordonamiento perimetral",
        ch.UnidadMetrado.M,
        "D1,D2,D3,D4",
        13,
        "",
    ),
    (
        "PROT_PEAT",
        ch.GrupoPartida.APUNT,
        "Protección peatonal / andamio fachada",
        ch.UnidadMetrado.M,
        "D2,D3",
        14,
        "",
    ),
    # —— Reparación / refuerzo de elementos ——
    ("REP_COL_LOCAL", ch.GrupoPartida.REP, "Reparación local de columna", ch.UnidadMetrado.UND, "D2", 20, "M1–M2"),
    ("REP_VIGA_LOCAL", ch.GrupoPartida.REP, "Reparación local de viga", ch.UnidadMetrado.UND, "D2", 21, ""),
    ("REP_LOSA", ch.GrupoPartida.REP, "Reparación / refuerzo de losa", ch.UnidadMetrado.M2, "D2", 22, ""),
    ("REF_COL", ch.GrupoPartida.REP, "Refuerzo de columna (encamisado / perfiles)", ch.UnidadMetrado.UND, "D2", 23, "M2–M4"),
    ("REF_VIGA", ch.GrupoPartida.REP, "Refuerzo de viga", ch.UnidadMetrado.UND, "D2", 24, ""),
    ("REF_MURO", ch.GrupoPartida.REP, "Refuerzo de muro / pantalla", ch.UnidadMetrado.M2, "D2", 25, ""),
    ("RECONS_PARCIAL", ch.GrupoPartida.REP, "Reconstrucción parcial de elemento", ch.UnidadMetrado.M3, "D2", 27, "M3–M4"),
    # —— Fisuras / grietas (detalle fino en procedimientos; pocas partidas) ——
    (
        "FIS_SELLADO",
        ch.GrupoPartida.FIS,
        "Sellado no estructural de fisuras / microfisuras",
        ch.UnidadMetrado.M,
        "D1,D2",
        28,
        "Acabados, tabiques, juntas; sin recuperar capacidad",
    ),
    (
        "INY_FISURA",
        ch.GrupoPartida.FIS,
        "Inyección estructural de fisuras",
        ch.UnidadMetrado.M,
        "D2",
        29,
        "Resina / lechada; recuperar monolitismo (VIG-01 / COL…)",
    ),
    (
        "FIS_COSIDO",
        ch.GrupoPartida.FIS,
        "Cosido / grapado de grietas estructurales",
        ch.UnidadMetrado.M,
        "D2",
        30,
        "Cuando la inyección sola no basta",
    ),
    (
        "FIS_CORTE",
        ch.GrupoPartida.FIS,
        "Tratamiento de grieta de corte (vigas / muros)",
        ch.UnidadMetrado.M,
        "D2",
        31,
        "Patrón sísmico diagonal; ver procedimiento aplicable",
    ),
    # —— Demolición / escombros ——
    ("DEM_PARCIAL", ch.GrupoPartida.DEM, "Demolición parcial controlada", ch.UnidadMetrado.M3, "D3", 40, ""),
    ("DEM_TOTAL", ch.GrupoPartida.DEM, "Demolición total del edificio", ch.UnidadMetrado.GLB, "D3,D4", 41, ""),
    ("DEM_FACHADA", ch.GrupoPartida.DEM, "Demolición / retiro de fachada", ch.UnidadMetrado.M2, "D2,D3", 42, ""),
    ("DEM_ELEMENTO", ch.GrupoPartida.DEM, "Demolición de elemento puntual", ch.UnidadMetrado.UND, "D2,D3", 43, ""),
    ("ESC_RETIRO", ch.GrupoPartida.ESC, "Retiro de escombros", ch.UnidadMetrado.M3, "D3,D4", 50, ""),
    ("ESC_TRANSP", ch.GrupoPartida.ESC, "Transporte / disposición de escombros", ch.UnidadMetrado.M3, "D3,D4", 51, ""),
    ("ESC_LIMPIEZA", ch.GrupoPartida.ESC, "Limpieza de lote post-demolición", ch.UnidadMetrado.M2, "D3,D4", 52, ""),
    # —— Estudios D1 ——
    ("EST_GEO", ch.GrupoPartida.EST, "Estudio geotécnico (GEO)", ch.UnidadMetrado.GLB, "D1", 60, ""),
    ("EST_ENS", ch.GrupoPartida.EST, "Ensayos de materiales (ENS)", ch.UnidadMetrado.UND, "D1", 61, ""),
    ("EST_MOD", ch.GrupoPartida.EST, "Modelo / análisis estructural (MOD)", ch.UnidadMetrado.GLB, "D1", 62, ""),
    ("EST_MON", ch.GrupoPartida.EST, "Monitoreo instrumentado (MON)", ch.UnidadMetrado.GLB, "D1", 63, ""),
    ("EST_INV", ch.GrupoPartida.EST, "Investigación elementos ocultos (INV)", ch.UnidadMetrado.GLB, "D1", 64, ""),
    ("EST_REI", ch.GrupoPartida.EST, "Reinspección programada (REI)", ch.UnidadMetrado.UND, "D1", 65, ""),
    ("EST_ALE", ch.GrupoPartida.EST, "Evaluación riesgo aledaños (ALE)", ch.UnidadMetrado.GLB, "D1", 66, ""),
    # —— Fachada / logística ——
    ("FAC_MAMPOST", ch.GrupoPartida.FAC, "Reparación / retiro mampostería", ch.UnidadMetrado.M2, "D2,D3", 70, ""),
    ("FAC_REVOQUE", ch.GrupoPartida.FAC, "Revoque / acabado fachada", ch.UnidadMetrado.M2, "D2", 71, ""),
    ("FAC_VIDRIO", ch.GrupoPartida.FAC, "Retiro elementos no estructurales en riesgo", ch.UnidadMetrado.UND, "D2,D3", 72, ""),
    ("MOV_EQUIPO", ch.GrupoPartida.MOV, "Movilización de equipo / grúa", ch.UnidadMetrado.GLB, "D2,D3,D4", 80, ""),
    ("MOV_VIGILANCIA", ch.GrupoPartida.MOV, "Vigilancia / custodia temporal", ch.UnidadMetrado.UND, "D1,D2,D3", 81, "días o turnos"),
    ("OTRO_PARTIDA", ch.GrupoPartida.OTRO, "Otra partida (detallar en nota)", ch.UnidadMetrado.GLB, "", 90, ""),
]


def asegurar_partidas_catalogo() -> int:
    from inspecciones.models import PartidaCatalogo

    n = 0
    for codigo, grupo, titulo, unidad, aplica, orden, desc in PARTIDAS_SEMILLA:
        obj, created = PartidaCatalogo.objects.update_or_create(
            codigo=codigo,
            defaults={
                "grupo": grupo,
                "titulo": titulo,
                "unidad_default": unidad,
                "aplica_decisiones": aplica,
                "orden": orden,
                "descripcion": desc,
                "activo": True,
            },
        )
        if created:
            n += 1
    return n


def listar_partidas_ayuda(*, limite: int | None = None) -> list[dict[str, str]]:
    """Lista activa para wizards / Excel (fallback a semilla si BD vacía)."""
    try:
        from django.apps import apps

        if apps.ready:
            from inspecciones.models import PartidaCatalogo

            qs = PartidaCatalogo.objects.filter(activo=True).order_by("orden", "codigo")
            if limite:
                qs = qs[:limite]
            rows = [
                {
                    "codigo": p.codigo,
                    "grupo": p.grupo,
                    "titulo": p.titulo,
                    "unidad": p.unidad_default,
                }
                for p in qs
            ]
            if rows:
                return rows
    except Exception:
        pass
    rows = [
        {
            "codigo": codigo,
            "grupo": grupo,
            "titulo": titulo,
            "unidad": unidad,
        }
        for codigo, grupo, titulo, unidad, _aplica, _orden, _desc in PARTIDAS_SEMILLA
    ]
    if limite:
        rows = rows[:limite]
    return rows
