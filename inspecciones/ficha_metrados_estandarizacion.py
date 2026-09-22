"""
Ficha MET-01 — Estandarización de partidas / metrados hacia COVENIN e ISO.
Vinculada a PLN-01 (plano de inspección): cada arreglo se ancla a un ID de elemento.
"""
from __future__ import annotations

from inspecciones import choices as ch
from inspecciones.partidas_catalogo import PARTIDAS_SEMILLA

_ANCLAS: dict[str, dict[str, str]] = {
    "APUNT_PREV": {
        "covenin": "Parte II.B prop. R2.6 · estabilización post-sísmica",
        "criterio": "Por piso o zona estabilizada. Distinto del shoring de trabajo.",
        "ajuste": "Alto — post-sísmico",
    },
    "APUNT_PISO": {
        "covenin": "Parte II.B prop. R2.6 Apuntalamiento",
        "criterio": "Medir por nivel durante la intervención; no confundir con APUNT_PREV.",
        "ajuste": "Alto — vacío II.B",
    },
    "APUNT_COL": {
        "covenin": "Parte II.B prop. R2.6",
        "criterio": "Una und = una columna; id_pln01 obligatorio (p. ej. PB-C6).",
        "ajuste": "Alto — vacío II.B",
    },
    "APUNT_VIGA": {
        "covenin": "Parte II.B prop. R2.6",
        "criterio": "Una und = un tramo; id_pln01 de viga (PLN-01).",
        "ajuste": "Alto — vacío II.B",
    },
    "ACORD_PERIM": {
        "covenin": "E11 provisionales / cercas (análogo)",
        "criterio": "Metro lineal de perímetro acordonado.",
        "ajuste": "Medio",
    },
    "PROT_PEAT": {
        "covenin": "E11 instalaciones provisionales",
        "criterio": "Metro lineal de protección peatonal / andamio de fachada.",
        "ajuste": "Medio",
    },
    "REP_COL_LOCAL": {
        "covenin": "Parte II.B prop. R3.1",
        "criterio": "Und por columna; id_pln01 = columna del plano.",
        "ajuste": "Alto — vacío II.B",
    },
    "REP_VIGA_LOCAL": {
        "covenin": "Parte II.B prop. R3.1",
        "criterio": "Und por tramo; id_pln01 de viga.",
        "ajuste": "Alto — vacío II.B",
    },
    "REP_LOSA": {
        "covenin": "Parte II.B prop. R3.1",
        "criterio": "m² de losa; referenciar ejes del paño en id_pln01/ubicacion.",
        "ajuste": "Alto — vacío II.B",
    },
    "REF_COL": {
        "covenin": "Parte II.B prop. R3.2 / R3.1",
        "criterio": "Und por columna reforzada; id_pln01.",
        "ajuste": "Alto — vacío II.B",
    },
    "REF_VIGA": {
        "covenin": "Parte II.B prop. R3.2 / R3.1",
        "criterio": "Und por tramo reforzado; id_pln01.",
        "ajuste": "Alto — vacío II.B",
    },
    "REF_MURO": {
        "covenin": "Parte II.B prop. R3.1",
        "criterio": "m²; id_pln01 de muro/pantalla.",
        "ajuste": "Alto — vacío II.B",
    },
    "RECONS_PARCIAL": {
        "covenin": "Parte II.B prop. R3",
        "criterio": "m³; id_pln01 del elemento reconstruido.",
        "ajuste": "Alto — vacío II.B",
    },
    "FIS_SELLADO": {
        "covenin": "Parte II.B prop. R4 (no estructural)",
        "criterio": "m de fisura sellada sin recuperar capacidad; id_pln01 si aplica.",
        "ajuste": "Medio",
    },
    "INY_FISURA": {
        "covenin": "Parte II.B prop. R3 (reparación CA)",
        "criterio": "m de fisura inyectada; id_pln01 del elemento portante.",
        "ajuste": "Alto — vacío II.B",
    },
    "FIS_COSIDO": {
        "covenin": "Parte II.B prop. R3",
        "criterio": "m de grieta cosida/grapada; id_pln01.",
        "ajuste": "Alto — vacío II.B",
    },
    "FIS_CORTE": {
        "covenin": "Parte II.B prop. R3",
        "criterio": "m de grieta de corte tratada; patrón sísmico; id_pln01.",
        "ajuste": "Alto — vacío II.B",
    },
    "DEM_PARCIAL": {
        "covenin": "E132… / E131 parcial",
        "criterio": "m³; id_pln01 del tramo demolido si es parcial.",
        "ajuste": "Bajo — COVENIN E13",
    },
    "DEM_TOTAL": {
        "covenin": "E131… (m²)",
        "criterio": "Preferir m²; glb solo sin plano.",
        "ajuste": "Medio — ajustar unidad",
    },
    "DEM_FACHADA": {
        "covenin": "E13 / E14",
        "criterio": "m² de fachada.",
        "ajuste": "Medio",
    },
    "DEM_ELEMENTO": {
        "covenin": "E132…",
        "criterio": "Preferir m³; id_pln01 del elemento.",
        "ajuste": "Medio",
    },
    "ESC_RETIRO": {
        "covenin": "E134… (m³ suelto)",
        "criterio": "Homologar con vol_escombros_m3 del caso.",
        "ajuste": "Bajo — quick win",
    },
    "ESC_TRANSP": {
        "covenin": "E903… (m³)",
        "criterio": "m³ suelto sobre camión.",
        "ajuste": "Bajo — quick win",
    },
    "ESC_LIMPIEZA": {
        "covenin": "E12 / E813 (análogo)",
        "criterio": "m² de lote.",
        "ajuste": "Medio",
    },
    "EST_GEO": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Complemento D1; no BoQ de intervención.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_ENS": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Und por ensayo; complemento D1.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_MOD": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Global; complemento D1.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_MON": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Global; complemento D1.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_INV": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Global; complemento D1.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_REI": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Und por reinspección.",
        "ajuste": "Bajo — separar capa",
    },
    "EST_ALE": {
        "covenin": "E01 (capa distinta)",
        "criterio": "Global; complemento D1.",
        "ajuste": "Bajo — separar capa",
    },
    "FAC_MAMPOST": {
        "covenin": "Parte II.B prop. R4 · E14",
        "criterio": "m²; id_pln01 si es paño localizado.",
        "ajuste": "Medio",
    },
    "FAC_REVOQUE": {
        "covenin": "Parte II.B prop. R4",
        "criterio": "m² de revoque.",
        "ajuste": "Medio",
    },
    "FAC_VIDRIO": {
        "covenin": "Parte II.B prop. R4.5",
        "criterio": "Und por elemento retirado.",
        "ajuste": "Medio",
    },
    "MOV_EQUIPO": {
        "covenin": "E11 / E9",
        "criterio": "Global; detallar equipo en nota.",
        "ajuste": "Medio",
    },
    "MOV_VIGILANCIA": {
        "covenin": "Provisional / memoria",
        "criterio": "Und = día o turno.",
        "ajuste": "Medio",
    },
    "OTRO_PARTIDA": {
        "covenin": "Sin código + memoria (COVENIN)",
        "criterio": "Nota obligatoria; evitar uso rutinario.",
        "ajuste": "Control",
    },
}


def _filas_catalogo() -> list[dict[str, str]]:
    rows = []
    for codigo, grupo, titulo, unidad, aplica, _orden, desc in PARTIDAS_SEMILLA:
        ancla = _ANCLAS.get(codigo) or {
            "covenin": "—",
            "criterio": "Definir ancla y criterio en revisión.",
            "ajuste": "Pendiente",
        }
        rows.append(
            {
                "codigo": codigo,
                "grupo": grupo.label if hasattr(grupo, "label") else str(grupo),
                "titulo": titulo,
                "unidad": unidad.label if hasattr(unidad, "label") else str(unidad),
                "aplica": aplica or "—",
                "desc": desc or "—",
                "covenin": ancla["covenin"],
                "criterio": ancla["criterio"],
                "ajuste": ancla["ajuste"],
            }
        )
    return rows


def ficha_met01() -> dict:
    return {
        "codigo": "MET-01",
        "categoria": "Metrados / partidas · vínculo PLN-01 · estandarización normativa",
        "titulo": (
            "Estandarización de partidas de metrado — acoplamiento a PLN-01 "
            "(plano de inspección), COVENIN 2000 e ISO/ICMS (Fase III)"
        ),
        "alcance": (
            "Definir el catálogo de partidas CPEH, su ancla normativa y —de forma "
            "obligatoria para elementos estructurales— el vínculo al plano PLN-01 "
            "mediante id_pln01 (mismo sistema de ejes e IDs que el croquis/plano "
            "de inspección). Objetivo: que cada arreglo quede atado a una sección "
            "del plano y pueda visualizarse de forma dinámica (seleccionar elemento "
            "→ asignar partida del catálogo). Complementa, no sustituye, el dictamen "
            "D1–D4 ni la ficha PLN-01."
        ),
        "jerga": (
            "PLN-01: plano de inspección con ejes letra×número e IDs de elemento "
            "(p. ej. PB-C6). id_pln01: campo del metrado que apunta a ese ID. "
            "Partida: código + descripción + unidad + criterio. Dual coding: código "
            "CPEH de campo + ancla COVENIN/R. Apuntamiento preventivo: estabilizar "
            "el edificio dañado post-sísmico; de trabajo: sostener durante la intervención."
        ),
        "borrador": True,
        "documento_relacionado": "PLN-01 — Plano de inspección estructural (ejes y mapa de estilo)",
        "aplicar_cuando": [
            "Se dibuja o usa el plano/croquis PLN-01 del caso.",
            "Se cuantifica intervención (metrado) en ficha, Excel o visor del plano.",
            "Se asigna un arreglo (partida) a un elemento concreto del plano.",
            "Se distingue apuntamiento preventivo vs de trabajo post-terremoto.",
            "Se prepara anteproyecto / estimación (cantidad × PU) para Fase III.",
            "Se homologa escombros (ESC_*) con vol_escombros_m3 y COVENIN E134/E903.",
        ],
        "no_aplicar": [
            "Sustituir COVENIN 1756 / 1756:2019 (evaluación sismorresistente).",
            "Sustituir el plan de apuntamiento calculado (gravedad + sismo temporal).",
            "Forzar códigos E… de obra nueva sobre reparación de existentes sin II.B.",
            "Crear partidas de fisura por cada ancho/tipo — usar procedimientos + nota.",
            "Usar como pliego contractual sin adopción formal del ente competente.",
        ],
        "especificacion": (
            "1) Leer primero PLN-01: el sistema de ejes y las reglas de ID "
            "(columna PB-C6; viga PB-V(A-B)·eje6; muro PB-M·ejeA·entre2-3) son la "
            "clave primaria espacial del metrado. 2) Toda línea de metrado sobre "
            "elemento estructural con cantidad > 0 debe llevar id_pln01 (y piso_pln). "
            "3) Flujo operativo: croquis/plano → identificar elemento → elegir partida "
            "del catálogo MET-01 → cantidad/unidad/confianza → (opcional) tipo_apuntamiento. "
            "4) Visor dinámico (Fase III): mapa SVG/plano interactivo; al seleccionar "
            "un nodo/tramo se abre el catálogo filtrado y se crea/edita LineaMetrado "
            "con ese id_pln01. 5) Apuntamiento: usar APUNT_PREV para estabilización "
            "post-sísmica; APUNT_PISO/COL/VIGA para shoring de trabajo; marcar "
            "tipo_apuntamiento. 6) Fisuras: FIS_SELLADO | INY_FISURA | FIS_COSIDO | "
            "FIS_CORTE (detalle en procedimientos). 7) Dual coding COVENIN/R e ICMS "
            "como capas superiores (ver secciones normativas)."
        ),
        "vinculo_pln01": [
            {
                "paso": "1",
                "titulo": "Plano / croquis PLN-01",
                "detalle": "Cada piso con ejes, norte, IDs de columnas/vigas/muros y daños.",
            },
            {
                "paso": "2",
                "titulo": "Seleccionar elemento",
                "detalle": "En campo (Excel/ficha) o en el visor: clic en nodo/tramo → id_pln01.",
            },
            {
                "paso": "3",
                "titulo": "Asignar partida MET-01",
                "detalle": "Catálogo filtrable por grupo (APUNT, FIS, REP…). Una o más líneas por elemento.",
            },
            {
                "paso": "4",
                "titulo": "Cuantificar",
                "detalle": "Cantidad, unidad, severidad, confianza, tipo_apuntamiento si aplica.",
            },
            {
                "paso": "5",
                "titulo": "Ver en el plano",
                "detalle": "El visor colorea/etiqueta elementos según partidas asignadas (arreglo por sección).",
            },
        ],
        "ids_pln01_ejemplos": [
            {"ejemplo": "PB-C6", "significa": "Columna en intersección de ejes, piso PB, nudo C-6"},
            {"ejemplo": "PB-V(A-B)·eje6", "significa": "Viga entre ejes A–B sobre el eje 6"},
            {"ejemplo": "PB-M·ejeA·entre2-3", "significa": "Muro sobre eje A entre líneas 2 y 3"},
            {"ejemplo": "P1-L·A3-B4", "significa": "Paño de losa referenciado por ejes (convención de brigada)"},
        ],
        "apuntamiento_post_sismico": [
            {
                "tipo": "Preventivo (APUNT_PREV)",
                "cuando": "Edificio dañado que debe estabilizarse ante gravedad y réplicas, antes o al margen de la reparación puntual.",
                "nota": "No sustituye el plan de apuntamiento dimensionado (protocolo / rehab sísmica).",
            },
            {
                "tipo": "De trabajo (APUNT_PISO / COL / VIGA)",
                "cuando": "Sostener vigas/losas/columnas mientras se inyecta, repara, refuerza o demuele localmente.",
                "nota": "Anclar cada und al id_pln01 del elemento apuntalado.",
            },
            {
                "tipo": "Acordonar / protección (ACORD_PERIM, PROT_PEAT)",
                "cuando": "Perímetro y peatones; complementa el apuntamiento estructural.",
                "nota": "Medición en m lineales.",
            },
        ],
        "capas_normativas": [
            {
                "capa": "0. Espacio del caso",
                "norma": "PLN-01 (ejes + IDs) + croquis adjunto",
                "rol": "Dónde está el daño / el arreglo",
            },
            {
                "capa": "1. Medición en campo",
                "norma": "Catálogo CPEH MET-01 + dictamen D1–D4",
                "rol": "Qué hacer y cuánto (partida + cantidad)",
            },
            {
                "capa": "2. Cómputo / presupuesto",
                "norma": "COVENIN 2000-92 · Parte II.B (R/P)",
                "rol": "Formalizar partida contractual",
            },
            {
                "capa": "3. Reporte",
                "norma": "ICMS 3 · ISO 12006-2",
                "rol": "Agregar costos a nivel proyecto",
            },
            {
                "capa": "4. Diseño estructural",
                "norma": "COVENIN 1756 / 1756:2019",
                "rol": "Justifica D/M; no define partidas",
            },
        ],
        "principios": [
            {
                "titulo": "PLN-01 es la clave espacial",
                "texto": (
                    "Sin id_pln01 el metrado no se puede pintar en el plano. "
                    "ubicacion libre es apoyo, no sustituto."
                ),
            },
            {
                "titulo": "Dual coding",
                "texto": (
                    "Conservar códigos CPEH en brigada; ancla COVENIN/R en catálogo "
                    "para Fase III."
                ),
            },
            {
                "titulo": "Apuntamiento post-sísmico explícito",
                "texto": (
                    "Separar preventivo vs trabajo; el metrado no reemplaza el cálculo "
                    "del sistema de shoring."
                ),
            },
            {
                "titulo": "Pocas partidas de fisura, muchos procedimientos",
                "texto": (
                    "FIS_SELLADO, INY_FISURA, FIS_COSIDO, FIS_CORTE; el detalle "
                    "(ancho, trayectoria) vive en el procedimiento + nota."
                ),
            },
            {
                "titulo": "Visor = misma verdad que Excel/ficha",
                "texto": (
                    "El mapa interactivo solo crea/edita LineaMetrado; no un silo paralelo."
                ),
            },
        ],
        "unidades_homologacion": [
            {
                "cpeh": "m, m², m³, und, kg",
                "covenin": "m, m², m³, pza, kgf (según partida)",
                "nota": "Aceptadas; und↔pza si hace falta.",
            },
            {
                "cpeh": "glb",
                "covenin": "Evitar; preferir m²/m³/pza",
                "nota": "DEM_TOTAL → m² (E131) con plano.",
            },
            {
                "cpeh": "piso",
                "covenin": "Equivalente a publicar (m² de nivel o und)",
                "nota": "APUNT_PREV / APUNT_PISO.",
            },
            {
                "cpeh": "m.l.",
                "covenin": "m",
                "nota": "Sinónimo operativo.",
            },
        ],
        "roadmap": [
            {
                "paso": "A",
                "titulo": "Campos id_pln01 en sistema",
                "detalle": "Hecho en LineaMetrado + Excel + admin (esta versión).",
            },
            {
                "paso": "B",
                "titulo": "Catálogo ampliado APUNT + FIS",
                "detalle": "APUNT_PREV y partidas de fisura; semilla actualizada.",
            },
            {
                "paso": "C",
                "titulo": "Visor interactivo (prototipo → prod)",
                "detalle": "SVG/plano por piso; clic elemento → partida; guarda LineaMetrado.",
            },
            {
                "paso": "D",
                "titulo": "Leyenda dinámica en el plano",
                "detalle": "Color por grupo de partida / severidad sobre nodos y tramos.",
            },
            {
                "paso": "E",
                "titulo": "Dual coding COVENIN + criterios por grupo",
                "detalle": "codigo_covenin/R y fichas de medición (E13 quick win).",
            },
            {
                "paso": "F",
                "titulo": "Vista ICMS (opcional)",
                "detalle": "Agregación gerencial sin cambiar captura de campo.",
            },
        ],
        "checklist": [
            "Existe plano/croquis PLN-01 del piso intervendo.",
            "id_pln01 presente en líneas estructurales con cantidad > 0.",
            "Partida del catálogo MET-01 (no texto libre como código).",
            "Si APUNT_*: tipo_apuntamiento = preventivo / trabajo / ambos.",
            "Fisuras: partida FIS_* correcta; detalle en procedimiento/nota.",
            "Unidad coherente con el catálogo.",
            "EST_* fuera del BoQ de intervención (o marcado complemento).",
            "El visor (cuando exista) muestra la misma línea que Excel/ficha.",
        ],
        "normativa_detalle": [
            {
                "codigo": "PLN-01 (CPEH)",
                "titulo": "Plano de inspección estructural — ejes y mapa de estilo",
                "para_que": "Identificar espacialmente daños y elementos.",
                "uso": "Fuente de id_pln01; MET-01 no redefine el dibujo, lo consume.",
            },
            {
                "codigo": "COVENIN-MINDUR 2000-92",
                "titulo": "Mediciones y codificación — Parte II.A",
                "para_que": "Cómputo y códigos E… (obra nueva / provisionales).",
                "uso": "Ancla E13/E134/E903 para DEM_* y ESC_*.",
            },
            {
                "codigo": "Parte II.B (anteproyecto)",
                "titulo": "Reparaciones de existentes (R… / P…)",
                "para_que": "Apuntamiento, reparación y refuerzo de existentes.",
                "uso": "Ancla para APUNT_*, REP_*, FIS_*, FAC_* bajo autoridad.",
            },
            {
                "codigo": "COVENIN 1756 / 1756:2019",
                "titulo": "Construcciones sismorresistentes",
                "para_que": "Evaluación / requisitos sísmicos.",
                "uso": "Justifica dictamen; no define partidas.",
            },
            {
                "codigo": "ICMS 3 / ISO 12006-2",
                "titulo": "Clasificación y reporte de costos / información",
                "para_que": "Agregar y comparar a nivel proyecto.",
                "uso": "Capa de reporte; no captura de campo.",
            },
        ],
        "riesgos": [
            {
                "riesgo": "Metrado sin id_pln01",
                "mitigacion": "No se puede mostrar en el plano; validar al elevar.",
            },
            {
                "riesgo": "Confundir APUNT_PREV con shoring de trabajo",
                "mitigacion": "Códigos separados + tipo_apuntamiento.",
            },
            {
                "riesgo": "Visor con datos distintos a Excel",
                "mitigacion": "Una sola tabla LineaMetrado como fuente de verdad.",
            },
            {
                "riesgo": "Inflar catálogo de fisuras",
                "mitigacion": "Solo 4 partidas FIS_*; resto en procedimientos.",
            },
        ],
        "filas_catalogo": _filas_catalogo(),
        "unidades_catalogo": [
            u.label for u in ch.UnidadMetrado if u != ch.UnidadMetrado.PENDIENTE
        ],
    }
