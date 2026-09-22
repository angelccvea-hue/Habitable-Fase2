"""Fichas técnicas PDF del catálogo de procedimientos (estilo guía Fase II)."""
from __future__ import annotations

from typing import Any

# Contenido alineado a la Guía práctica / lineamientos técnicos CPEH (ago. 2026).
# Estructura común: código, título, categoría, alcance, aplicar_cuando[], no_aplicar[],
# especificacion, referencias, notas.

FICHAS: dict[str, dict[str, Any]] = {
    "VIG-01": {
        "codigo": "VIG-01",
        "categoria": "Vigas",
        "titulo": "Inyección estructural de fisuras en vigas",
        "alcance": (
            "Recuperar monolitismo en vigas de concreto armado con fisuras de flexión "
            "o corte de abertura limitada, sin pérdida de núcleo."
        ),
        "aplicar_cuando": [
            "Grietas por flexión sismorresistente (verticales en zona de máximo momento).",
            "Aberturas de grieta inferiores a 5,0 mm sin desprendimiento de concreto.",
            "Ausencia de grietas diagonales críticas por corte cerca de los apoyos.",
        ],
        "no_aplicar": [
            "Rótula plástica con pérdida total de recubrimiento.",
            "Aplastamiento del núcleo o pérdida de altura efectiva.",
            "Grietas diagonales severas por corte (> 2 mm con afectación del núcleo).",
        ],
        "especificacion": (
            "Diseñar el nivel de descarga provisional e inyectar con resina de baja viscosidad "
            "o lechada cementicia fluida para recuperar el monolitismo. Documentar ubicación "
            "por piso y ejes (p. ej. PB-V(A-B)·eje6)."
        ),
    },
    "VIG-02": {
        "codigo": "VIG-02",
        "categoria": "Vigas",
        "titulo": "Reparación localizada de recubrimiento en vigas",
        "alcance": "Restituir recubrimiento y proteger acero en zonas con pérdida localizada.",
        "aplicar_cuando": [
            "Desprendimiento del concreto en cara inferior o laterales.",
            "Núcleo superior e inferior estable; estribos cerrados intactos.",
        ],
        "no_aplicar": [
            "Barras pandeadas o estribos abiertos.",
            "Pérdida severa de sección o núcleo triturado.",
        ],
        "especificacion": (
            "Instalar apuntalamiento temporal en vigas y losas tributarias. Cortar bordes a 20 mm, "
            "limpiar cabillas, aplicar puente de adherencia y restituir la sección mediante mortero "
            "tixotrópico o bombeo de microconcreto en encofrados estancos con venteos."
        ),
    },
    "VIG-03": {
        "codigo": "VIG-03",
        "categoria": "Vigas",
        "titulo": "Reconstrucción de rótula plástica",
        "alcance": "Reconstruir zonas de rótula plástica bajo descarga diseñada.",
        "aplicar_cuando": [
            "Formación de rótula plástica con pérdida total del recubrimiento.",
            "Concentración de daño inelástico en extremos de viga.",
        ],
        "no_aplicar": [
            "Solo fisuras superficiales reparables con VIG-01 / VIG-02.",
        ],
        "especificacion": (
            "Apuntalar de forma sismorresistente la viga y las losas a ambos lados. "
            "Instalar conectores de corte anclados al núcleo con resina epóxica. "
            "Vaciar con microconcreto autocompactante o mortero fluido sin contracción."
        ),
    },
    "VIG-04": {
        "codigo": "VIG-04",
        "categoria": "Vigas",
        "titulo": "Reconstrucción de núcleo en vigas",
        "alcance": "Sustituir o reconstruir el núcleo comprimido con confinamiento adecuado.",
        "aplicar_cuando": [
            "Aplastamiento del núcleo de concreto o pérdida de altura efectiva.",
            "Grietas diagonales severas por corte con afectación del núcleo.",
        ],
        "no_aplicar": [
            "Daño limitado al recubrimiento sin compromiso del núcleo (usar VIG-02).",
        ],
        "especificacion": (
            "Apuntalar, demoler concreto dañado, restablecer armadura y confinamiento, "
            "vaciar con grout/microconcreto de retracción compensada. Registrar ejes y piso."
        ),
    },
    "COL-01": {
        "codigo": "COL-01",
        "categoria": "Columnas",
        "titulo": "Sellado y protección superficial en columnas",
        "alcance": "Tratamiento de fisuras superficiales sin atribuir recuperación de capacidad.",
        "aplicar_cuando": [
            "Grietas superficiales o de retracción térmica/hidráulica.",
            "Sin patrón sísmico (ni diagonales ni aplastamiento).",
            "Acero transversal y longitudinal no expuesto.",
        ],
        "no_aplicar": [
            "Grietas asociadas a flexión/corte sísmico (usar COL-02+).",
            "Acero expuesto o núcleo comprometido.",
        ],
        "especificacion": (
            "Aplicar puente de adherencia y sellador elastomérico industrial. "
            "No atribuir recuperación de capacidad estructural en el informe. "
            "Identificar columna por piso y eje (p. ej. PB-C6)."
        ),
    },
    "COL-02": {
        "codigo": "COL-02",
        "categoria": "Columnas",
        "titulo": "Inyección estructural en columnas",
        "alcance": "Inyectar fisuras con núcleo intacto y acero competente.",
        "aplicar_cuando": [
            "Grietas transversales u horizontales asociadas a flexión por sismo.",
            "Abertura visible entre 0,05 mm y 5,0 mm.",
            "Núcleo confinado intacto (sin trituración ni desprendimiento).",
            "Acero longitudinal y estribos rectos, competentes y alineados.",
        ],
        "no_aplicar": [
            "Barras pandeadas, estribos abiertos o núcleo triturado.",
        ],
        "especificacion": (
            "Inyección continua a baja presión (de abajo hacia arriba) con resina epóxica "
            "de baja viscosidad (grietas < 2 mm) o lechada cementicia con superplastificante "
            "(5 mm ≥ grietas ≥ 2 mm)."
        ),
    },
    "COL-03": {
        "codigo": "COL-03",
        "categoria": "Columnas",
        "titulo": "Reparación localizada de recubrimiento en columnas",
        "alcance": "Reponer recubrimiento con núcleo sano y barras sin pandeo.",
        "aplicar_cuando": [
            "Desprendimiento o desconchamiento del concreto de recubrimiento.",
            "Núcleo confinado sano y sin fisuras profundas.",
            "Estribos y barras expuestos pero sin deformación ni pandeo.",
            "Pérdida de sección por corrosión/daño en barras < 25%.",
        ],
        "no_aplicar": [
            "Aplastamiento del núcleo o barras pandeadas (COL-04 / COL-CRIT).",
        ],
        "especificacion": (
            "Delimitar con corte de disco a 20 mm, escarificar, limpiar acero, "
            "condición saturada-superficialmente-seca, puente de adherencia epóxico y "
            "reponer con mortero estructural tixotrópico reforzado con fibras."
        ),
    },
    "COL-04": {
        "codigo": "COL-04",
        "categoria": "Columnas",
        "titulo": "Reconstrucción equivalente bajo descarga diseñada",
        "alcance": "Reconstruir sección con apuntalamiento y descarga calculada.",
        "aplicar_cuando": [
            "Aplastamiento localizado o trituración del núcleo confinado.",
            "Barras longitudinales pandeadas/deformadas o estribos abiertos.",
            "Pérdida severa de sección o barras fracturadas.",
        ],
        "no_aplicar": [
            "Daño reparable con COL-01 a COL-03.",
            "Desplome / acortamiento generalizado (COL-CRIT).",
        ],
        "especificacion": (
            "Instalar apuntalamiento estructural y transferir cargas antes de intervenir. "
            "Demoler concreto dañado, sustituir tramos de cabilla (conectores o solapes), "
            "reponer estribos a 135° y vaciar con grout fluido f′c ≈ 300 kgf/cm²."
        ),
    },
    "COL-05": {
        "codigo": "COL-05",
        "categoria": "Columnas",
        "titulo": "Refuerzo o encamisado de columnas",
        "alcance": "Recuperar capacidad mediante encamisado, confinamiento o refuerzo externo.",
        "aplicar_cuando": [
            "Se requiere aumentar capacidad o confinamiento tras reparación.",
            "Diagnóstico indica insuficiencia residual frente a demandas esperadas.",
        ],
        "no_aplicar": [
            "Elemento fuera de alcance de reparación (COL-CRIT).",
        ],
        "especificacion": (
            "Diseñar encamisado (concreto o perfiles), anclajes y secuencia bajo descarga. "
            "Documentar ejes, piso y justificación respecto a COVENIN 1756 vigente."
        ),
    },
    "COL-CRIT": {
        "codigo": "COL-CRIT",
        "categoria": "Columnas",
        "titulo": "Condición crítica — fuera de alcance de reparación simple",
        "alcance": "Declarar elemento no reparable por métodos COL-01 a COL-04.",
        "aplicar_cuando": [
            "Gran acortamiento del miembro o desplome.",
            "Daño severo generalizado / núcleo triturado generalizado.",
        ],
        "no_aplicar": [
            "Casos cubiertos por COL-01 a COL-05.",
        ],
        "especificacion": (
            "El elemento no es reparable por métodos simples. Elevar decisión D/M con "
            "evidencia fotográfica, croquis de ejes y respaldo de coordinación/revisión."
        ),
    },
    "MAM-01": {
        "codigo": "MAM-01",
        "categoria": "Mampostería",
        "titulo": "Reparación no estructural de fisuras leves",
        "alcance": "Sellado de microfisuras en acabados o juntas, sin daño de piezas.",
        "aplicar_cuando": [
            "Microfisuras o fisuras finas superficiales aisladas e inactivas (ancho < 0,5 mm).",
            "Fisuras solo en acabado/juntas, sin rotura ni trituración de bloques.",
            "Sin desalineaciones ni desplazamientos del paño.",
        ],
        "no_aplicar": [
            "Grietas 0,5–5 mm (MAM-02) o daño severo (MAM-03/MAM-04).",
        ],
        "especificacion": (
            "Retirar friso suelto en franja ≥ 10 cm a cada lado. Limpiar abertura. "
            "Sellar con masilla/elastómero de poliuretano (evitar silicona si se pintará). "
            "Reponer acabado con mortero base y estuco compatible."
        ),
    },
    "MAM-02": {
        "codigo": "MAM-02",
        "categoria": "Mampostería",
        "titulo": "Inyección estructural en mampostería",
        "alcance": "Inyectar grietas moderadas sin desplome apreciable.",
        "aplicar_cuando": [
            "Grietas por tracción/flexión entre 0,5 mm y 5,0 mm.",
            "Mortero agrietado sin trituración de piezas.",
            "Sin desplome apreciable del paño.",
        ],
        "no_aplicar": [
            "Grietas > 5 mm con piezas fracturadas (MAM-03).",
            "Paños en rutas de evacuación con daño moderado-severo (MAM-04).",
        ],
        "especificacion": (
            "Remover acabado 10–30 cm a cada lado. Instalar puertos de inyección. "
            "Sellar cara externa entre boquillas. Inyectar de abajo hacia arriba "
            "(resina baja viscosidad o lechada sin contracción, según tipo de pieza)."
        ),
    },
    "MAM-03": {
        "codigo": "MAM-03",
        "categoria": "Mampostería",
        "titulo": "Reconstrucción localizada (llaveado y costura)",
        "alcance": "Reconstruir paños con daño severo localizado sin riesgo de volcamiento.",
        "aplicar_cuando": [
            "Grietas diagonales o en «X» de 5–15 mm.",
            "Piezas localmente fracturadas sin comprometer estabilidad global.",
            "Desplome < 1 % de la altura del muro.",
        ],
        "no_aplicar": [
            "Rutas de evacuación (preferir MAM-04).",
            "Desplome ≥ 1 % h (riesgo de volcamiento).",
        ],
        "especificacion": (
            "Costura: grapas/barras helicoidales Ø6 mm en juntas. "
            "Llaveado: retirar piezas fracturadas solo con herramientas manuales; "
            "reposicionar unidades equivalentes; curado húmedo 3–5 días."
        ),
    },
    "MAM-04": {
        "codigo": "MAM-04",
        "categoria": "Mampostería",
        "titulo": "Sustitución por tabiquería liviana sismorresistente",
        "alcance": "Reemplazar mampostería dañada en rutas de evacuación por sistema liviano.",
        "aplicar_cuando": [
            "Paño colindante con escaleras, pasillos o rutas de escape con daño moderado a severo.",
        ],
        "no_aplicar": [
            "Reconstrucción con bloques de arcilla/concreto en rutas de escape (prohibido).",
        ],
        "especificacion": (
            "Demoler de arriba hacia abajo. Sistema en seco RF-120: perfiles galvanizados ≥ 0,90 mm, "
            "unión telescópica a losas, núcleo lana mineral ≥ 40 kg/m³, placas cementicia + yeso Tipo X "
            "según lineamiento técnico de mampostería post-sismo."
        ),
    },
    "PLN-01": {
        "codigo": "PLN-01",
        "categoria": "Planos de inspección",
        "titulo": (
            "Plano de inspección estructural en planta "
            "(sistema de ejes / matriz) — borrador para revisión"
        ),
        "alcance": (
            "Homologar el entregable gráfico de la inspección Fase II: un "
            "plano de inspección estructural en planta (no un croquis libre "
            "sin ejes) que declare el sistema de ejes, permita identificar "
            "plenamente cada daño y case evidencia / procedimientos con la "
            "estructura declarada en el sistema."
        ),
        "jerga": (
            "Según COVENIN 107:1980, el croquis (esquema) es un dibujo "
            "preliminar, a menudo a mano alzada, que explica una idea y "
            "puede no guardar proporciones. El plano es el documento técnico "
            "de construcción/inspección preparado para uso operativo "
            "(COVENIN 3476/3477 hablan de «dibujos y planos»). "
            "En Fase II se exige plano de inspección en planta con ejes; "
            "el croquis de campo solo se admite como borrador previo que "
            "debe pasarse a plano antes de elevar el caso."
        ),
        "aplicar_cuando": [
            "Elaborar o actualizar el plano de inspección en planta del piso "
            "revisado (mínimo un plano por caso al elevar).",
            "Referenciar daños del §6 (columnas, vigas, muros, losas) a un "
            "identificador único de eje / nudo / tramo.",
            "Distribuir plantilla CAD (DXF/DWG) o SVG a brigadas.",
            "Plantas irregulares (en L, C, U, con juntas, torres gemelas): "
            "usar la misma regla de ejes, con ejes auxiliares si hace falta.",
        ],
        "no_aplicar": [
            "Sustituir el dictamen D/M ni la evaluación sismorresistente "
            "(eso corresponde a COVENIN 1756 / 1756:2019).",
            "Si existe plano estructural de proyecto verificado, adoptar su "
            "nomenclatura de ejes y registrar equivalencias; no inventar "
            "otra matriz que contradiga el proyecto.",
            "Entregar solo un croquis sin ejes, sin norte o sin identificación "
            "de piso (no cumple esta ficha).",
        ],
        "especificacion": (
            "1) Título del documento: «Plano de inspección estructural — "
            "planta [piso]». 2) Trazar sistema de ejes: letras en un sentido "
            "y números en el otro (burbujas); ejes principales ortogonales; "
            "ejes auxiliares con apóstrofe (p. ej. B′, 3′) si hay desfaces. "
            "3) Columnas en intersecciones; vigas como tramos entre ejes; "
            "muros/pantallas como tramos o alineaciones. 4) Obligatorio: "
            "norte, nombre del edificio, ID Habitable, piso (PB, P1…). "
            "5) Leyenda de daños (nivel A/B/C y/o código de procedimiento). "
            "6) Capas mínimas: EJES, COLUMNAS, VIGAS, MUROS, DANOS, NORTE, "
            "ROTULO. 7) Identificadores: columna PB-C6; viga PB-V(A-B)·eje6; "
            "muro PB-M·ejeA·entre2-3. 8) Plantas irregulares: ver sección "
            "de ejemplos (L, C, junta sísmica, volados)."
        ),
        "normativa_detalle": [
            {
                "codigo": "COVENIN 107:1980",
                "titulo": "Dibujo técnico. Definiciones",
                "para_que": (
                    "Define croquis/esquema frente a dibujo definitivo. "
                    "Fija que el croquis es preliminar y puede no guardar "
                    "proporciones."
                ),
                "uso_en_pln01": (
                    "Justifica llamar «plano de inspección» al entregable "
                    "oficial y limitar el croquis a etapa de campo previa."
                ),
            },
            {
                "codigo": "COVENIN 3466:1999",
                "titulo": "Representación de vistas, secciones y cortes",
                "para_que": (
                    "Reglas de cómo se representan plantas, alzados y cortes "
                    "en dibujo de ingeniería civil y arquitectura."
                ),
                "uso_en_pln01": (
                    "La vista principal del entregable es la planta "
                    "(sección horizontal). Cortes solo si aclaran un daño "
                    "vertical (p. ej. columna en elevación)."
                ),
            },
            {
                "codigo": "COVENIN 3467:1999",
                "titulo": "Líneas de referencias",
                "para_que": (
                    "Cómo se trazan y usan líneas de referencia en el dibujo."
                ),
                "uso_en_pln01": (
                    "Los ejes estructurales son el sistema de líneas de "
                    "referencia para ubicar daños y elementos."
                ),
            },
            {
                "codigo": "COVENIN 3469:1999",
                "titulo": "Designación de construcciones y partes",
                "para_que": (
                    "Sistema de designación (nombres/códigos) de la "
                    "edificación y de sus partes (afín a ISO 4157)."
                ),
                "uso_en_pln01": (
                    "Cada daño y cada elemento debe tener un ID único "
                    "(piso + eje/nudo/tramo), no solo una descripción libre."
                ),
            },
            {
                "codigo": "COVENIN 3470:1999",
                "titulo": "Designación — habitaciones y otras áreas",
                "para_que": "Designación de locales y áreas interiores.",
                "uso_en_pln01": (
                    "Opcional: asociar el daño a un local (p. ej. PB-hall) "
                    "además del eje, cuando ayude a la brigada."
                ),
            },
            {
                "codigo": "COVENIN 3472:1999",
                "titulo": "Armadura de concreto. Simbología",
                "para_que": "Símbolos de armadura en planos estructurales.",
                "uso_en_pln01": (
                    "Solo si el plano de inspección detalla cabillas "
                    "expuestas; no es obligatorio en el croquis de campo "
                    "pasado a plano simplificado."
                ),
            },
            {
                "codigo": "COVENIN 3473–3475:1999",
                "titulo": "Coordinación modular y cuadrículas",
                "para_que": (
                    "Vocabulario, principios y representación de "
                    "dimensiones, líneas y cuadrículas modulares."
                ),
                "uso_en_pln01": (
                    "Fundamento de la «matriz» de ejes: cuadrícula de "
                    "referencia espacial, aunque la planta no sea un "
                    "rectángulo perfecto."
                ),
            },
            {
                "codigo": "COVENIN 3476 / 3477:1999",
                "titulo": "Formato y plegado de dibujos y planos",
                "para_que": (
                    "Formato de hoja, rotulado y plegado de planos."
                ),
                "uso_en_pln01": (
                    "El archivo/plantilla debe identificar institución, "
                    "código PLN-01, edificio, piso, fecha y autor en el "
                    "rótulo (cajetín)."
                ),
            },
            {
                "codigo": "COVENIN 1756 / 1756:2019",
                "titulo": "Edificaciones sismorresistentes",
                "para_que": (
                    "Criterios de análisis, diseño y evaluación "
                    "sismorresistente (incluye irregularidades)."
                ),
                "uso_en_pln01": (
                    "No define cómo dibujar el plano de inspección. Sí "
                    "motiva registrar irregularidades en planta "
                    "(L, C, juntas, etc.) porque afectan el diagnóstico; "
                    "el plano debe hacerlas visibles."
                ),
            },
        ],
        "ejemplos_irregulares": [
            {
                "nombre": "0) Planta rectangular (referencia base — estilo Carimar)",
                "descripcion": (
                    "Pórtico regular A–C × 1–7. Cada intersección = columna "
                    "(cuadrado azul). Círculos = severidad en nudo; "
                    "rectángulos = tramo de viga; recuadro magenta = flecha."
                ),
                "como_ejes": (
                    "Letras × números con burbujas. Norte/Calle/Entrada "
                    "obligatorios. Mismo lenguaje gráfico que el plano de campo."
                ),
                "ejemplo_dano": (
                    "Columnas B6/A6/C6 y bordes 7 y 1 · vigas en ejes 7, 6 y 1 · "
                    "flechas en B entre 6–7 y 2–3 (como Residencias Carimar I)."
                ),
                "plano": {
                    "titulo": "EJEMPLO — PLANTA RECTANGULAR (estilo Carimar)",
                    "cols": ["A", "B", "C"],
                    "rows": ["7", "6", "5", "4", "3", "2", "1"],
                    "nodos": {
                        "7A": "col_bc", "7B": "col_a", "7C": "col_bc",
                        "6A": "col_bc", "6B": "col_a", "6C": "col_bc",
                        "5A": "col_a", "5B": "col_a", "5C": "col_a",
                        "4A": "col_a", "4B": "col_a", "4C": "col_a",
                        "3A": "col_a", "3B": "col_a", "3C": "col_a",
                        "2A": "col_a", "2B": "col_a", "2C": "col_a",
                        "1A": "col_a", "1B": "col_a", "1C": "col_a",
                    },
                    "tramos": [
                        {"fila": "7", "de": "A", "a": "B", "nivel": "bc"},
                        {"fila": "7", "de": "B", "a": "C", "nivel": "bc"},
                        {"fila": "6", "de": "A", "a": "B", "nivel": "bc"},
                        {"fila": "6", "de": "B", "a": "C", "nivel": "bc"},
                        {"fila": "2", "de": "A", "a": "B", "nivel": "a"},
                        {"fila": "1", "de": "A", "a": "B", "nivel": "bc"},
                        {"fila": "1", "de": "B", "a": "C", "nivel": "bc"},
                    ],
                    "flechas": [
                        {"eje": "B", "entre": ("6", "7")},
                        {"eje": "B", "entre": ("2", "3")},
                    ],
                    "orientacion": {
                        "arriba": "OESTE",
                        "abajo": "ESTE",
                        "izq": "SUR",
                        "der": "NORTE",
                    },
                    "entrada": "1C",
                    "nota_pie": (
                        "ID ej.: PB-B6 · PB-V(A-B)·eje6 · PB-FLECHA·B·entre6-7"
                    ),
                },
            },
            {
                "nombre": "1) Planta en L (dos alas)",
                "descripcion": (
                    "Ala vertical (A–B, ejes 1–5) + ala horizontal (A–D, ejes 4–5). "
                    "La esquina reentrante (B4) suele concentrar daño."
                ),
                "como_ejes": (
                    "Una sola matriz global. Sin columnas fuera de la L. "
                    "Mismo simbolismo (cuadrado / círculo / tramo)."
                ),
                "ejemplo_dano": (
                    "Columna reentrante PB-B4 — nivel B. "
                    "Viga ala corta PB-V(B-C)·eje4."
                ),
                "plano": {
                    "titulo": "EJEMPLO — PLANTA EN L",
                    "cols": ["A", "B", "C", "D"],
                    "rows": ["5", "4", "3", "2", "1"],
                    "vacios": [
                        "5C", "5D", "3C", "3D", "2C", "2D", "1C", "1D",
                    ],
                    "nodos": {
                        "5A": "col", "5B": "col",
                        "4A": "col", "4B": "col_bc", "4C": "col", "4D": "col",
                        "3A": "col", "3B": "col",
                        "2A": "col", "2B": "col",
                        "1A": "col", "1B": "col",
                    },
                    "tramos": [
                        {"fila": "4", "de": "B", "a": "C", "nivel": "bc"},
                        {"fila": "4", "de": "C", "a": "D", "nivel": "a"},
                    ],
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": "Sin nudo = fuera de la L. Rojo = PB-B4.",
                },
            },
            {
                "nombre": "2) Planta en C / U (patio o vacío central)",
                "descripcion": (
                    "Crujías perimetrales alrededor de un vacío/patio. "
                    "La cuadrícula envuelve el vacío sin renumerar."
                ),
                "como_ejes": (
                    "Mantener A–D / 1–4 globales. Patio sin columnas."
                ),
                "ejemplo_dano": (
                    "Columna borde patio PB-D3. "
                    "Muro PB-M·ejeB·entre2-3."
                ),
                "plano": {
                    "titulo": "EJEMPLO — PLANTA EN C / U",
                    "cols": ["A", "B", "C", "D"],
                    "rows": ["4", "3", "2", "1"],
                    "vacios": ["3B", "3C", "2B", "2C"],
                    "nodos": {
                        "4A": "col", "4B": "col", "4C": "col", "4D": "col",
                        "3A": "col", "3D": "col_bc",
                        "2A": "col", "2D": "col",
                        "1A": "col", "1B": "col", "1C": "col", "1D": "col",
                    },
                    "tramos_vert": [
                        {"eje": "B", "de": "2", "a": "3", "nivel": "a"},
                    ],
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": "Centro vacío = patio. Rojo = PB-D3.",
                },
            },
            {
                "nombre": "3) Dos cuerpos / torres con junta",
                "descripcion": (
                    "Torre 1 y Torre 2 separadas por junta sísmica. "
                    "Prefijo T1- / T2- en el ID."
                ),
                "como_ejes": (
                    "Franja JUNTA sin columnas. Ejes propios por cuerpo."
                ),
                "ejemplo_dano": (
                    "T2-PB-A2 — nivel C — COL-04."
                ),
                "plano": {
                    "titulo": "EJEMPLO — DOS CUERPOS CON JUNTA",
                    "cols": ["T1-A", "T1-B", "JUNTA", "T2-A", "T2-B"],
                    "rows": ["3", "2", "1"],
                    "nodos": {
                        "3T1-A": "col", "3T1-B": "col",
                        "3T2-A": "col", "3T2-B": "col",
                        "2T1-A": "col", "2T1-B": "col",
                        "2T2-A": "col_bc", "2T2-B": "col",
                        "1T1-A": "col", "1T1-B": "col",
                        "1T2-A": "col", "1T2-B": "col",
                    },
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": "Amarillo = junta. Rojo = T2-PB-A2.",
                },
            },
            {
                "nombre": "4) Volado / desface (eje auxiliar)",
                "descripcion": (
                    "Núcleo A–C × 1–3 con volado hacia B′."
                ),
                "como_ejes": (
                    "Eje auxiliar B′ (burbuja). Acotar desface B→B′."
                ),
                "ejemplo_dano": (
                    "Apoyo volado PB-B′2. Losa PB-LOSA·entre-B/B′·eje2."
                ),
                "plano": {
                    "titulo": "EJEMPLO — VOLADO CON EJE B′",
                    "cols": ["A", "B", "C", "B′"],
                    "rows": ["3", "2", "1"],
                    "vacios": ["3B′"],
                    "nodos": {
                        "3A": "col", "3B": "col", "3C": "col",
                        "2A": "col", "2B": "col", "2C": "col", "2B′": "col_bc",
                        "1A": "col", "1B": "col", "1C": "col", "1B′": "col_a",
                    },
                    "flechas": [
                        {"eje": "B′", "entre": ("1", "2"), "label": "Flecha"},
                    ],
                    "tramos": [
                        {"fila": "2", "de": "C", "a": "B′", "nivel": "a"},
                    ],
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": "B′ auxiliar. Rojo = PB-B′2.",
                },
            },
            {
                "nombre": "5) Planta trapezoidal / no ortogonal",
                "descripcion": (
                    "Pórticos que no forman 90°. En CAD los ejes van sesgados; "
                    "aquí se ordenan IDs con el mismo simbolismo."
                ),
                "como_ejes": (
                    "Rotular A–D / 1–3. Nota: «ejes según pórticos reales»."
                ),
                "ejemplo_dano": (
                    "Nudo PB-D2. Viga PB-V(C-D)·eje2 — nivel B."
                ),
                "plano": {
                    "titulo": "EJEMPLO — TRAPECIO (IDs; CAD sesgado)",
                    "cols": ["A", "B", "C", "D"],
                    "rows": ["3", "2", "1"],
                    "vacios": ["3D", "1A"],
                    "nodos": {
                        "3A": "col", "3B": "col", "3C": "col",
                        "2A": "col", "2B": "col", "2C": "col", "2D": "col_bc",
                        "1B": "col", "1C": "col", "1D": "col",
                    },
                    "tramos": [
                        {"fila": "2", "de": "C", "a": "D", "nivel": "bc"},
                    ],
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": "Vacíos = fuera del trapecio. Rojo = PB-D2.",
                },
            },
        ],
        "contenido_plantilla": [
            "Rótulo (cajetín): institución, PLN-01, edificio, ID Habitable, "
            "piso, fecha, elaboró/revisó.",
            "Planta con sistema de ejes (letras × números) y norte "
            "(o referencia Calle / Entrada).",
            "Aplicar el mapa de estilo (leyenda gráfica) de esta ficha.",
            "Tabla de daños: ID · elemento · nivel A/B/C · procedimiento · "
            "foto.",
            "Si la planta es irregular: nota de tipología (L/C/junta/volado) "
            "y lista de ejes auxiliares (A′, D′…).",
            "Plantilla CAD de referencia: archivo DXF "
            "«PLN-01-plano-inspeccion-ejes» (capas EJES, COLUMNAS, VIGAS, "
            "MUROS, DANOS, NORTE, ROTULO + leyenda). Abrir en AutoCAD / "
            "LibreCAD / DraftSight; guardar como DWG si el flujo del "
            "equipo lo exige. El término «.cad» en campo = DWG o DXF.",
            "Formato de archivo preferido: DXF/DWG o PDF vectorial; SVG "
            "aceptable para plantilla liviana.",
            "Estado: borrador para mesa técnica hasta adopción formal.",
        ],
        "plantilla_cad": {
            "formato": "DXF R2010",
            "archivo": "PLN-01-plano-inspeccion-ejes.dxf",
            "nota": (
                "Intercambio abierto alineado a esta ficha. Convertir a "
                "DWG en AutoCAD si se requiere entrega nativa."
            ),
        },
        "mapa_estilo": {
            "titulo": "Mapa de estilo — plano de inspección (leyenda gráfica)",
            "intro": (
                "Lenguaje visual propuesto para homologar planos como los de "
                "campo (p. ej. Carimar, Cabo Coral): mismos símbolos, mismos "
                "colores, misma forma de rotular ejes y daños."
            ),
            "capas": [
                {
                    "simbolo": "titulo",
                    "nombre": "Título del edificio",
                    "regla": "Texto azul oscuro (#00247D), centrado arriba, mayúsculas o título del inmueble.",
                },
                {
                    "simbolo": "eje",
                    "nombre": "Burbuja de eje",
                    "regla": (
                        "Círculo con letra o número (A, B, 1, 2…). Color "
                        "magenta/rosa de identificación. Ejes auxiliares: A′, D′."
                    ),
                },
                {
                    "simbolo": "grid",
                    "nombre": "Líneas de eje",
                    "regla": "Línea discontinua gris/azul fino entre burbujas (retícula).",
                },
                {
                    "simbolo": "col",
                    "nombre": "Columna / nudo (sin daño destacado)",
                    "regla": "Cuadrado azul en la intersección de ejes.",
                },
                {
                    "simbolo": "col_a",
                    "nombre": "Columna — daño leve / observar (nivel A)",
                    "regla": "Círculo amarillo alrededor del nudo (o relleno amarillo suave).",
                },
                {
                    "simbolo": "col_bc",
                    "nombre": "Columna — daño moderado/severo (nivel B o C)",
                    "regla": "Círculo rojo alrededor del nudo.",
                },
                {
                    "simbolo": "tramo_a",
                    "nombre": "Tramo viga/muro — daño leve (A)",
                    "regla": "Rectángulo amarillo entre dos nudos (vano).",
                },
                {
                    "simbolo": "tramo_bc",
                    "nombre": "Tramo viga/muro — daño B/C o crítico",
                    "regla": "Rectángulo rojo entre dos nudos.",
                },
                {
                    "simbolo": "flecha",
                    "nombre": "Flecha / deflexión de losa o viga",
                    "regla": (
                        "Recuadro magenta con texto «Flecha» en el vano "
                        "afectado; en tabla anotar mm e ID (p. ej. PB-LOSA·B·entre6-7)."
                    ),
                },
                {
                    "simbolo": "orient",
                    "nombre": "Orientación",
                    "regla": (
                        "Norte / Sur / Este / Oeste en rojo, o al menos "
                        "«Calle» y «Entrada» si el norte no está claro."
                    ),
                },
                {
                    "simbolo": "cota",
                    "nombre": "Cotas (opcional)",
                    "regla": "Medidas entre ejes en metros (p. ej. 22,2 / 11,3) cuando aporten contexto.",
                },
            ],
            "reglas_id": [
                "Todo símbolo de daño debe tener ID único en la tabla: "
                "columna PB-B6 · viga PB-V(A-B)·eje2 · flecha PB-FLECHA·ejeB·entre6-7.",
                "Amarillo = leve/observar (A). Rojo = moderado-severo (B/C). "
                "No usar otros colores para severidad.",
                "No dibujar daño sin eje: prohibido «fachada norte» sin ID.",
                "Si hay foto, el pie de foto repite el mismo ID.",
            ],
            "mini_ejemplo": {
                "plano": {
                    "titulo": "MINI-EJEMPLO — MAPA DE ESTILO",
                    "cols": ["A", "B", "C"],
                    "rows": ["3", "2", "1"],
                    "nodos": {
                        "3A": "col_bc", "3B": "col_a", "3C": "col",
                        "2A": "col", "2B": "col", "2C": "col",
                        "1A": "col", "1B": "col_a", "1C": "col_bc",
                    },
                    "tramos": [
                        {"fila": "2", "de": "A", "a": "B", "nivel": "a"},
                        {"fila": "2", "de": "B", "a": "C", "nivel": "bc"},
                    ],
                    "flechas": [
                        {"eje": "B", "entre": ("2", "3")},
                    ],
                    "orientacion": {
                        "arriba": "N",
                        "abajo": "S",
                        "izq": "O",
                        "der": "E",
                    },
                    "nota_pie": (
                        "3A/1C = col B/C · 3B/1B = col A · tramos en eje 2 · "
                        "flecha en B entre 2–3"
                    ),
                },
            },
        },
        "normativa": [
            "COVENIN 107:1980 — croquis ≠ plano (jerga).",
            "COVENIN 3466–3477:1999 — familia de dibujo técnico "
            "civil/arquitectura (vistas, referencias, designación, "
            "modularidad, formato de planos).",
            "COVENIN 1756 / 1756:2019 — evaluación sismorresistente "
            "(contexto; no es norma de dibujo del plano de inspección).",
        ],
        "borrador": True,
    },
}

REFERENCIAS_COMUNES = [
    "Comisión Presidencial — Lineamientos técnicos: Evaluación y reparación de elementos "
    "de concreto armado con daño leve y moderado por sismo.",
    "Comisión Presidencial — Lineamientos técnicos: Evaluación, reparación y restitución "
    "de paredes de mampostería dañadas por sismo.",
    "Comisión Presidencial — Lineamientos técnicos: Apuntalamiento de columnas, vigas y losas.",
    "FUNVISIS — Evaluación rápida de daños en edificaciones (Informe técnico vigente).",
]


def ficha_para(codigo: str) -> dict[str, Any] | None:
    from inspecciones.plano_estilo_svg import enriquecer_plano, plano_a_svg

    raw = FICHAS.get((codigo or "").strip().upper())
    if not raw:
        return None
    ficha = dict(raw)
    ejemplos = []
    for ej in ficha.get("ejemplos_irregulares") or []:
        ej2 = dict(ej)
        if ej.get("plano"):
            ej2["svg_html"] = plano_a_svg(ej["plano"])
            ej2["nota_pie"] = ej["plano"].get("nota_pie") or ""
        ejemplos.append(ej2)
    if ejemplos:
        ficha["ejemplos_irregulares"] = ejemplos
    me = ficha.get("mapa_estilo")
    if me and me.get("mini_ejemplo"):
        me = dict(me)
        me["mini_ejemplo"] = enriquecer_plano(me["mini_ejemplo"])
        ficha["mapa_estilo"] = me
    return ficha


def listar_codigos_con_ficha() -> list[str]:
    return sorted(FICHAS.keys())
