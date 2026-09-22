"""Generación de plantillas Excel — informe (vertical) y lote (filas)."""
from __future__ import annotations

import io
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from django.db import models
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from inspecciones.field_hints import FIELD_HINTS
from inspecciones.models import CasoRojo
from inspecciones.section_labels import CASE_FIELDSETS

PLANTILLA_VERSION = "v1.10-sin-evidencia-excel"
INSTITUCION = "Comisión Presidencial para la Evaluación de Habitabilidad de Infraestructuras"
PROGRAMA = "Verificación Habitable — Fase II"
# Contraseña de protección de hojas (solo admin TI la quita si hace falta ajustar plantilla).
SHEET_PROTECT_PASSWORD = "cpeh"
# Filas vacías extra en Metrados (además de las precargadas) para agregar líneas sin insertar filas.
METRADOS_FILAS_EXTRA = 12

# Colores de pestaña (openpyxl: RGB sin #)
TAB_PORTADA = "00247D"
TAB_RELLENAR = "2E7D32"  # verde — pestaña a completar
TAB_METRADOS = "F9A825"  # ámbar — pestaña a completar
TAB_REF = "78909C"  # gris — solo consulta (ocultas en v1.8)
# Zona fuera del formulario (estilo “solo lo que debe cargar”)
FILL_FUERA_FORMULARIO = PatternFill("solid", fgColor="9E9E9E")

LISTAS: dict[str, list[str]] = {
    "si_no_parcial": ["Sí", "No", "Parcial / corregir", "Pendiente"],
    "si_no_insuf": ["Sí", "No", "Insuficiente evidencia", "Pendiente"],
    # Se sincroniza con Estado2daRonda en _sync_listas_estado()
    "estado_2da": [
        "Pendiente verificación",
        "En visita",
        "Borrador",
        "Pendiente revisión",
        "Revisado",
        "Aprobado",
        "Publicado",
    ],
    "decision_D": [
        "D1 — Complementos requeridos",
        "D2 — Reparar / reconstruir",
        "D3 — Demoler",
        "D4 — Escombros / ya colapsado",
        "Pendiente",
    ],
    "magnitud_M": [
        "N/A (no es D2)",
        "M1 — Reparación local (menor intervención)",
        "M2 — Reparación importante",
        "M3 — Reconstrucción parcial",
        "M4 — Reconstrucción / refuerzo mayor (mayor intervención)",
        "Pendiente",
    ],
    "complementos_ejemplo": [
        "GEO,REI",
        "ENS,MOD",
        "MON,INV",
        "ALE,OTR",
    ],
    "prioridad": ["Inmediata", "Alta", "Programable", "Pendiente"],
    "abc": ["A", "B", "C", "No observable", "Pendiente"],
    "ocupacion": [
        "Desalojado",
        "Ocupación parcial",
        "Habitado irregularmente",
        "Escombros",
        "Pendiente",
    ],
    "sistema": [
        "Pórticos concreto armado",
        "Muros de concreto",
        "Mixto",
        "Acero",
        "Mampostería",
        "Otro",
        "Pendiente",
    ],
    "pct_columnas": ["No observable", "<10%", "10–30%", ">30%", ">50%", "Pendiente"],
    "inclinacion": [
        "No",
        "Sí — cualitativa",
        "Sí — con medición Δ",
        "No observable",
        "Pendiente",
    ],
    "peligro_aledanos": ["Sí", "No", "No observable", "Pendiente"],
    "confianza_metrado": ["Alta", "Media", "Estimada", "Pendiente"],
    "elemento_metrado": [
        "Columna",
        "Viga",
        "Muro / pantalla",
        "Losa",
        "Escalera",
        "Fachada",
        "Sótano / semisótano",
        "Cimentación",
        "Edificio completo",
        "Entorno / vía",
        "Otro",
        "Pendiente",
    ],
    "accion_metrado": [
        "Apuntalar / shoring",
        "Reparar",
        "Reforzar",
        "Demoler",
        "Retirar / desmontar",
        "Acordonar / proteger",
        "Monitorear",
        "Estudio / ensayo",
        "Otro",
        "Pendiente",
    ],
    "unidad_metrado": ["m", "m²", "m³", "und", "kg", "m.l.", "glb", "piso", "Pendiente"],
    "tipo_apuntamiento": ["preventivo", "trabajo", "ambos", "na"],
}

LISTA_BY_FIELD: dict[str, str] = {
    "val_edificio": "si_no_parcial",
    "val_etiqueta": "si_no_insuf",
    "val_geometria": "si_no_parcial",
    "val_ranking": "si_no_parcial",
    "sistema": "sistema",
    "ocupacion": "ocupacion",
    "peligro_aledanos": "peligro_aledanos",
    "pct_columnas": "pct_columnas",
    "pct_estructura_intervenir": "pct_columnas",
    "metrado_confianza": "confianza_metrado",
    "inclinacion": "inclinacion",
    "dano_vigas": "abc",
    "dano_losas": "abc",
    "riesgo_fachada": "abc",
    "col_nivel": "abc",
    "vig_nivel": "abc",
    "mur_nivel": "abc",
    "los_nivel": "abc",
    "mam_nivel": "abc",
    "repar_viable": "si_no_insuf",
    "estado_2da": "estado_2da",
    "decision_D": "decision_D",
    "magnitud_M": "magnitud_M",
    "prioridad": "prioridad",
}

PRECARGA_FIELDS = frozenset(
    {
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
        "score",
        "banda",
        "puestos",
        "score_detalle",
        "prob_rel",
    }
)

VISITA_PENDIENTE: dict[str, str] = {
    "val_edificio": "Pendiente",
    "val_etiqueta": "Pendiente",
    "val_geometria": "Pendiente",
    "val_ranking": "Pendiente",
    "sistema": "Pendiente",
    "ocupacion": "Pendiente",
    "peligro_aledanos": "Pendiente",
    "pct_columnas": "Pendiente",
    "inclinacion": "Pendiente",
    "dano_vigas": "Pendiente",
    "dano_losas": "Pendiente",
    "riesgo_fachada": "Pendiente",
    "col_nivel": "Pendiente",
    "vig_nivel": "Pendiente",
    "mur_nivel": "Pendiente",
    "los_nivel": "Pendiente",
    "mam_nivel": "Pendiente",
    "repar_viable": "Pendiente",
    "estado_2da": "En visita",
    "decision_D": "Pendiente",
    "magnitud_M": "Pendiente",
    "prioridad": "Pendiente",
}

SKIP_EXPORT_FIELDS = frozenset(
    {
        "inspector_asignado",
        "revisor_asignado",
        "coordinador_asignado",
        "created_at",
        "updated_at",
        "lat",
        "lng",
        # §11 Evidencia: solo en ficha web (fotos, croquis, firmas)
        "n_fotos",
        "firmas",
    }
)

# Secciones del fieldset que no van al Excel (se cargan solo en el sistema).
SKIP_EXPORT_SECTIONS = frozenset(
    {
        "11 — Evidencia, croquis y firmas",
    }
)

TALL_TEXT_FIELDS = frozenset(
    {
        "obs_f1",
        "score_detalle",
        "correcciones",
        "metrado_notas",
        "analisis_libre",
        "col_evidencia",
        "vig_evidencia",
        "mur_evidencia",
        "los_evidencia",
        "escaleras",
        "preexistentes",
        "mam_diag",
        "proc_codigos",
        "proc_notas",
        "medidas",
        "justificacion",
        "resumen_ejecutivo",
    }
)


def _build_rows_def() -> list[tuple[str, str | None, str | None, str | None, bool]]:
    rows: list[tuple[str, str | None, str | None, str | None, bool]] = []
    for section_title, opts in CASE_FIELDSETS:
        if "Auditoría" in section_title:
            continue
        if section_title in SKIP_EXPORT_SECTIONS or section_title.startswith("11 —"):
            continue
        rows.append((section_title, None, None, None, False))
        for fname in opts["fields"]:
            if fname in SKIP_EXPORT_FIELDS:
                continue
            field = CasoRojo._meta.get_field(fname)
            label = str(field.verbose_name)
            lista = LISTA_BY_FIELD.get(fname)
            precarga = fname in PRECARGA_FIELDS
            rows.append((section_title, label, fname, lista, precarga))
    return rows


ROWS_DEF = _build_rows_def()
EXPORT_COLUMNS = [r[2] for r in ROWS_DEF if r[2]]


def _fmt_value(val: Any) -> Any:
    if val is None:
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, models.Model):
        return str(val)
    return val


def caso_to_dict(caso: CasoRojo, *, plantilla_visita: bool = True) -> dict[str, Any]:
    """Convierte caso a dict para Excel. Si plantilla_visita, limpia campos de visita no llenos."""
    data: dict[str, Any] = {}
    for col in EXPORT_COLUMNS:
        data[col] = _fmt_value(getattr(caso, col, ""))

    if plantilla_visita:
        for key, default in VISITA_PENDIENTE.items():
            cur = data.get(key, "")
            if cur in ("", "Pendiente", None):
                data[key] = default
        for key in EXPORT_COLUMNS:
            if key in PRECARGA_FIELDS or key in VISITA_PENDIENTE:
                continue
            if data.get(key) in ("", None):
                data[key] = ""

    data["_hab_id"] = caso.hab_id
    data["_nombre"] = caso.nombre_conf or caso.nombre_hab or ""
    return data


def _sheet_name_safe(hab_id: int, nombre: str = "") -> str:
    base = f"{hab_id}"
    if nombre:
        slug = re.sub(r"[^\w\s-]", "", nombre)[:12].strip().replace(" ", "_")
        if slug:
            base = f"{hab_id}_{slug}"
    return base[:31]


def _thin_border() -> Border:
    side = Side(style="thin", color="CCCCCC")
    return Border(left=side, right=side, top=side, bottom=side)


def _section_fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _add_tricolor_bar(ws, row: int = 1) -> None:
    colors = ("FFCC00", "00247D", "CF142B")
    widths = (12, 12, 12)
    col = 1
    for color, w in zip(colors, widths):
        c = ws.cell(row, col, "")
        c.fill = PatternFill("solid", fgColor=color)
        ws.column_dimensions[get_column_letter(col)].width = w
        col += 1
    ws.row_dimensions[row].height = 6


def _sync_listas_estado() -> None:
    """Alinea LISTAS['estado_2da'] con el catálogo oficial del modelo."""
    from inspecciones import choices as ch

    LISTAS["estado_2da"] = [c.value for c in ch.Estado2daRonda]


def estados_para_excel(caso: CasoRojo, user=None) -> list[str]:
    """
    Valores del desplegable «Cambio de estado» en la plantilla:
    estado actual + siguientes permitidos (mismo criterio que el combo web).
    """
    from inspecciones import choices as ch
    from inspecciones.workflow import TRANSICIONES, opciones_estado_2da

    actual = (getattr(caso, "estado_2da", None) or "").strip() or ch.Estado2daRonda.PENDIENTE
    if user is not None:
        return [v for v, _lbl in opciones_estado_2da(user, actual)]
    permitidos = {actual} | set(TRANSICIONES.get(actual, set()))
    return [v for v in ch.Estado2daRonda.values if v in permitidos]


def _dv_valores_explicitos(valores: list[str], sqref: str) -> DataValidation:
    """Lista corta embebida (por caso) — evita estados ajenos al flujo actual."""
    limpios = [str(v).replace('"', "") for v in valores if v]
    formula = '"' + ",".join(limpios) + '"'
    return _dv(formula, sqref)


def _hint_for_field(fname: str, *, es_precarga: bool, lista_key: str | None) -> str:
    if fname == "estado_2da":
        return (
            "Solo etapas del flujo de este caso (actual + siguiente permitido por su rol). "
            "Al cargar el Excel se valida la transición; no se aceptan saltos."
        )
    if fname in FIELD_HINTS:
        return FIELD_HINTS[fname]
    if es_precarga:
        return "Precarga — validar en sitio; no reescribir salvo error (use §3)."
    if lista_key:
        return "Elija un valor de la lista desplegable (celda amarilla)."
    return "Escriba según lo observado en la visita 2."


def _set_tab_color(ws, rgb: str) -> None:
    ws.sheet_properties.tabColor = rgb


def _aplicar_vista_limpia(ws, *, max_col: int, max_row: int, extra_cols: int = 18, extra_rows: int = 35) -> None:
    """
    Oculta la «hoja vacía» de Excel: sin cuadrícula y zona gris fuera del formulario.
    El operador solo ve columnas/filas de trabajo.
    """
    ws.sheet_view.showGridLines = False
    # Columnas a la derecha del formulario
    for col in range(max_col + 1, max_col + 1 + extra_cols):
        letter = get_column_letter(col)
        ws.column_dimensions[letter].width = 2.5
        for row in range(1, max_row + extra_rows + 1):
            ws.cell(row=row, column=col).fill = FILL_FUERA_FORMULARIO
    # Filas debajo del contenido útil
    for row in range(max_row + 1, max_row + 1 + extra_rows):
        ws.row_dimensions[row].height = 12
        for col in range(1, max_col + 1):
            cell = ws.cell(row=row, column=col)
            if cell.value in (None, ""):
                cell.fill = FILL_FUERA_FORMULARIO


def _write_portada(
    wb: Workbook,
    titulo: str,
    subtitulo: str,
    notas: list[tuple[str, str]],
    *,
    pestanas_rellenar: list[str] | None = None,
) -> None:
    ws = wb.active
    ws.title = "Portada"
    _set_tab_color(ws, TAB_PORTADA)
    _add_tricolor_bar(ws, 1)

    ws["A3"] = titulo
    ws["A3"].font = Font(name="Calibri", size=16, bold=True, color="00247D")
    ws.merge_cells("A3:E3")
    ws["A4"] = INSTITUCION
    ws["A4"].font = Font(name="Calibri", size=10, color="475569")
    ws.merge_cells("A4:E4")
    ws["A5"] = subtitulo
    ws["A5"].font = Font(name="Calibri", size=11, bold=True, color="1F4E79")
    ws.merge_cells("A5:E5")

    r = 7
    ws.cell(r, 1, "▶ QUÉ DEBE RELLENAR")
    ws.cell(r, 1).font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    ws.cell(r, 1).fill = PatternFill("solid", fgColor="2E7D32")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    r += 1

    pestanas = pestanas_rellenar or []
    if pestanas:
        texto_pest = (
            "Solo verá estas pestañas de trabajo (el resto está oculto):\n"
            + "\n".join(f"  • «{p}»" for p in pestanas)
            + "\nLos códigos de partida van en el desplegable de Metrados; "
            "los procedimientos se marcan Sí/No en su pestaña."
        )
    else:
        texto_pest = (
            "Complete la hoja del edificio (pestaña verde) y, si aplica, la hoja «Metrados» (ámbar)."
        )
    ws.cell(r, 1, texto_pest)
    ws.cell(r, 1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(r, 1).fill = PatternFill("solid", fgColor="E8F5E9")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    ws.row_dimensions[r].height = 72
    r += 2

    ws.cell(r, 1, "Pasos recomendados")
    ws.cell(r, 1).font = Font(name="Calibri", size=11, bold=True, color="00247D")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    r += 1

    pasos = [
        "1) Abra la pestaña VERDE del edificio (nombre ≈ ID + nombre corto).",
        "2) Solo puede editar la columna B de secciones 3–10 y 12 (amarillo/blanco). El resto de la hoja está en gris.",
        "3) Secciones 1–2 (azul): solo lea y valide. Si hay error, use §3 «valor correcto».",
        "4) NO hay §11 en este Excel: fotos, croquis y firmas se cargan solo en la ficha web.",
        "5) Columna C «Cómo llenar»: ayuda (no se importa).",
        "6) Condicionales al elevar: inclinación con Δ → Δ; daño A/B/C → mecanismo + evidencia; D1/D2 según reglas.",
        "7) Metrados (ámbar): columnas B–K. Procedimientos: solo columna Sí/No.",
        "8) Guarde y cárguelo (Cargar Excel llenado). Luego adjunte fotos/croquis en la ficha (≥3 fotos, ≥1 croquis).",
    ]
    for paso in pasos:
        ws.cell(r, 1, paso)
        ws.cell(r, 1).alignment = Alignment(wrap_text=True)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        ws.row_dimensions[r].height = 22
        r += 1

    r += 1
    ws.cell(r, 1, "Leyenda de colores (en la hoja del edificio)")
    ws.cell(r, 1).font = Font(name="Calibri", size=11, bold=True, color="00247D")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    r += 1

    leyenda = [
        ("D9E2F3", "Azul claro", "Precarga Habitable / ranking — bloqueada; solo validar"),
        ("FFF2CC", "Amarillo", "Lista desplegable — editable (columna Valor)"),
        ("FFFFFF", "Blanco", "Texto libre — editable (columna Valor)"),
        ("E2EFDA", "Verde suave (col. C)", "Ayuda — bloqueada; no se importa"),
    ]
    for color, nombre, desc in leyenda:
        ws.cell(r, 1, "").fill = PatternFill("solid", fgColor=color)
        ws.cell(r, 1).border = _thin_border()
        ws.cell(r, 2, nombre).font = Font(bold=True, size=10)
        ws.cell(r, 3, desc).alignment = Alignment(wrap_text=True)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        r += 1

    r += 1
    ws.cell(r, 1, "Política de decisión (recordatorio)")
    ws.cell(r, 1).font = Font(name="Calibri", size=11, bold=True, color="00247D")
    r += 1
    ws.cell(
        r,
        1,
        "Por regla del programa: D2 reparar (o D1 si faltan estudios). "
        "D3/D4 demolición / escombros = última instancia. "
        "Al elevar, el sistema exige los mismos campos obligatorios/condicionales que esta plantilla indica en «Cómo llenar». "
        "Hojas protegidas (v1.8): solo pestañas de trabajo visibles; "
        "edite celdas desbloqueadas; no desproteja la precarga azul.",
    )
    ws.cell(r, 1).alignment = Alignment(wrap_text=True)
    ws.cell(r, 1).fill = PatternFill("solid", fgColor="FFF8E1")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    ws.row_dimensions[r].height = 36
    r += 2

    for tit, txt in notas:
        ws.cell(r, 1, tit).font = Font(name="Calibri", size=10, bold=True)
        ws.cell(r, 1).fill = PatternFill("solid", fgColor="EEF2F8")
        ws.cell(r, 2, txt).alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        ws.row_dimensions[r].height = 40
        r += 1

    ws.cell(r, 1, "plantilla_version")
    ws.cell(r, 2, PLANTILLA_VERSION)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 28
    ws.column_dimensions["E"].width = 28
    _aplicar_vista_limpia(ws, max_col=5, max_row=max(r, 28))
    _proteger_hoja(ws, solo_consulta=True)


def _unlock_cell(cell) -> None:
    """Celda editable cuando la hoja está protegida."""
    cell.protection = Protection(locked=False)


def _proteger_hoja(ws, *, solo_consulta: bool = False) -> None:
    """
    Activa protección de hoja.

    En openpyxl/OOXML, True = la acción queda PROHIBIDA al usuario.
    - solo_consulta=True: Portada, catálogos, listas (sin celdas editables).
    - solo_consulta=False: solo celdas con _unlock_cell son editables.

    Bug v1.6: selectUnlockedCells=True impedía seleccionar/editar las celdas
    desbloqueadas (Excel mostraba «hoja protegida» al escribir en B–K).
    """
    prot = ws.protection
    prot.sheet = True
    prot.password = SHEET_PROTECT_PASSWORD
    prot.enable()
    # Permitir selección (False = no prohibir)
    prot.selectLockedCells = False
    prot.selectUnlockedCells = False
    if solo_consulta:
        return
    # Hojas de relleno: permitir tipografía básica y filas nuevas en rangos útiles
    prot.formatCells = False
    prot.insertRows = False
    prot.deleteRows = False
    prot.sort = False
    prot.autoFilter = False


def _add_list_sheet(wb: Workbook) -> None:
    """Listas fijas + columnas dinámicas de códigos de partida y procedimiento."""
    from inspecciones.catalogo_procedimientos import (
        asegurar_procedimientos_catalogo,
        listar_procedimientos_ayuda,
    )
    from inspecciones.partidas_catalogo import asegurar_partidas_catalogo, listar_partidas_ayuda

    _sync_listas_estado()
    try:
        asegurar_partidas_catalogo()
        asegurar_procedimientos_catalogo()
    except Exception:
        pass

    name = "Listas_desplegables"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    col_i = 1
    for key, values in LISTAS.items():
        ws.cell(1, col_i, key)
        for row_i, val in enumerate(values, start=2):
            ws.cell(row_i, col_i, val)
        col_i += 1

    # Códigos de partida (para DV en Metrados)
    ws.cell(1, col_i, "codigo_partida")
    partidas = [r["codigo"] for r in listar_partidas_ayuda()]
    for row_i, val in enumerate(partidas, start=2):
        ws.cell(row_i, col_i, val)
    wb._cpeh_list_cols = {k: i + 1 for i, k in enumerate(LISTAS.keys())}
    wb._cpeh_list_cols["codigo_partida"] = col_i
    wb._cpeh_n_partidas = len(partidas)
    col_i += 1

    # Códigos de procedimiento (referencia / DV auxiliares)
    ws.cell(1, col_i, "codigo_proc")
    procs = [r["codigo"] for r in listar_procedimientos_ayuda()]
    for row_i, val in enumerate(procs, start=2):
        ws.cell(row_i, col_i, val)
    wb._cpeh_list_cols["codigo_proc"] = col_i
    wb._cpeh_n_procs = len(procs)

    ws.sheet_state = "hidden"
    _proteger_hoja(ws, solo_consulta=True)


def _dv(formula: str, sqref: str) -> DataValidation:
    dv = DataValidation(
        type="list",
        formula1=formula,
        allow_blank=True,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="Valor no válido",
        error="Elija un valor de la lista.",
    )
    dv.add(sqref)
    return dv


def _write_informe_sheet(
    wb: Workbook,
    sheet_name: str,
    data: dict[str, Any],
    *,
    titulo: str | None = None,
    estados_dropdown: list[str] | None = None,
) -> None:
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]
    ws = wb.create_sheet(sheet_name)
    _set_tab_color(ws, TAB_RELLENAR)
    thin = _thin_border()
    font_title = Font(name="Calibri", size=14, bold=True, color="00247D")
    font_sec = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_lab = Font(name="Calibri", size=10, bold=True)
    font_val = Font(name="Calibri", size=10)
    font_note = Font(name="Calibri", size=9, italic=True, color="666666")
    font_hint = Font(name="Calibri", size=8, color="33691E")
    hint_fill = PatternFill("solid", fgColor="E2EFDA")

    ws["A1"] = titulo or f"INFORME — ID {data.get('hab_id', data.get('_hab_id', ''))}"
    ws["A1"].font = font_title
    ws.merge_cells("A1:C1")
    ws["A2"] = (
        "PESTAÑA PROTEGIDA — solo edite la columna B (Valor) en secciones 3–10 y 12. "
        "§11 Evidencia (fotos/croquis/firmas) NO va en este Excel: solo en la ficha web. "
        "Azul (§1–2) y columnas A/C están bloqueadas. Amarillo = lista · Blanco = texto. "
        "Condicionales: inclinación con Δ → Δ obligatorio; daño A/B/C → mecanismo + evidencia; "
        "D1 → complementos; D2 → magnitud M. Al terminar: Cargar Excel llenado."
    )
    ws["A2"].font = font_note
    ws["A2"].fill = PatternFill("solid", fgColor="E8F5E9")
    ws.merge_cells("A2:C2")
    ws.row_dimensions[2].height = 42

    ws["A3"] = "Campo"
    ws["B3"] = "Valor (rellene aquí)"
    ws["C3"] = "Cómo llenar"
    for col in (1, 2, 3):
        ws.cell(3, col).font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        ws.cell(3, col).fill = PatternFill("solid", fgColor="2E7D32")

    dropdown_cells: list[tuple[int, str]] = []
    estado_row: int | None = None
    r = 4
    for seccion, etiqueta, key, lista_key, es_precarga in ROWS_DEF:
        if etiqueta is None:
            if seccion.startswith(("1 —", "2 —")):
                titulo_sec = f"{seccion}  ·  SOLO VALIDAR (azul)"
                fill_sec = "546E7A"
            elif seccion.startswith("3 —"):
                titulo_sec = f"{seccion}  ·  RELLENAR (listas + correcciones si aplica)"
                fill_sec = "2E7D32"
            elif seccion.startswith("9 —"):
                titulo_sec = f"{seccion}  ·  RELLENAR totales aquí + líneas en pestaña Metrados"
                fill_sec = "F9A825"
            elif seccion.startswith("10 —"):
                titulo_sec = f"{seccion}  ·  RELLENAR (por regla: D2 reparar)"
                fill_sec = "2E7D32"
            else:
                titulo_sec = f"{seccion}  ·  RELLENAR EN VISITA 2"
                fill_sec = "2E75B6"
            ws.cell(r, 1, titulo_sec)
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
            cell = ws.cell(r, 1)
            cell.fill = _section_fill(fill_sec)
            cell.font = font_sec
            r += 1
            continue
        ws.cell(r, 1, etiqueta).font = font_lab
        ws.cell(r, 1).border = thin
        val = data.get(key, "")
        c = ws.cell(r, 2, val)
        c.font = font_val
        c.border = thin
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if es_precarga:
            c.fill = PatternFill("solid", fgColor="D9E2F3")
        else:
            # Solo valores de visita/dictamen son editables bajo protección
            _unlock_cell(c)
        if key == "estado_2da" and estados_dropdown:
            estado_row = r
            if not es_precarga:
                c.fill = PatternFill("solid", fgColor="FFF2CC")
        elif lista_key:
            dropdown_cells.append((r, lista_key))
            if not es_precarga:
                c.fill = PatternFill("solid", fgColor="FFF2CC")
        hint = _hint_for_field(key or "", es_precarga=es_precarga, lista_key=lista_key)
        h = ws.cell(r, 3, hint)
        h.font = font_hint
        h.fill = hint_fill
        h.alignment = Alignment(wrap_text=True, vertical="top")
        h.border = thin
        if key in TALL_TEXT_FIELDS:
            ws.row_dimensions[r].height = 55
        else:
            ws.row_dimensions[r].height = 28
        r += 1

    list_cols = getattr(wb, "_cpeh_list_cols", None) or {
        k: i + 1 for i, k in enumerate(LISTAS.keys())
    }
    for row_i, lista_key in dropdown_cells:
        col_i = list_cols[lista_key]
        col_letter = get_column_letter(col_i)
        nvals = len(LISTAS.get(lista_key, [])) or 1
        formula = f"Listas_desplegables!${col_letter}$2:${col_letter}${nvals + 1}"
        ws.add_data_validation(_dv(formula, f"$B${row_i}"))

    if estado_row is not None and estados_dropdown:
        ws.add_data_validation(_dv_valores_explicitos(estados_dropdown, f"$B${estado_row}"))

    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 42
    ws.column_dimensions["C"].width = 48
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A4"
    _aplicar_vista_limpia(ws, max_col=3, max_row=max(r, 20))
    _proteger_hoja(ws)


def _write_lote_sheet(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    name = "Lote_informes"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    _set_tab_color(ws, TAB_RELLENAR)
    header_fill = PatternFill("solid", fgColor="2E7D32")
    header_font = Font(color="FFFFFF", bold=True, name="Calibri", size=9)
    precarga_fill = PatternFill("solid", fgColor="D9E2F3")
    lista_fill = PatternFill("solid", fgColor="FFF2CC")

    labels = []
    for _sec, etiqueta, key, lista_key, es_precarga in ROWS_DEF:
        if key:
            labels.append((key, etiqueta, lista_key, es_precarga))

    for col_i, (key, label, _lk, _pre) in enumerate(labels, start=1):
        ws.cell(1, col_i, key).font = header_font
        ws.cell(1, col_i).fill = header_fill
        ws.cell(2, col_i, label).font = Font(bold=True, size=9)
        ws.column_dimensions[get_column_letter(col_i)].width = min(24, max(12, len(label) + 2))

    list_cols = {k: i + 1 for i, k in enumerate(LISTAS.keys())}
    for row_idx, data in enumerate(rows, start=3):
        for col_i, (key, _label, lista_key, es_precarga) in enumerate(labels, start=1):
            val = data.get(key, "")
            c = ws.cell(row_idx, col_i, val)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if es_precarga:
                c.fill = precarga_fill
            elif lista_key:
                c.fill = lista_fill
                lk = list_cols.get(lista_key)
                if lk:
                    col_letter = get_column_letter(lk)
                    nvals = len(LISTAS[lista_key])
                    formula = f"Listas_desplegables!${col_letter}$2:${col_letter}${nvals + 1}"
                    ws.add_data_validation(_dv(formula, f"{get_column_letter(col_i)}{row_idx}"))

    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(len(labels))}{max(3, len(rows) + 2)}"
    # Solo celdas de visita (no precarga) editables
    for row_idx in range(3, 3 + len(rows)):
        for col_i, (_key, _label, _lista_key, es_precarga) in enumerate(labels, start=1):
            if not es_precarga:
                _unlock_cell(ws.cell(row_idx, col_i))
    last_row = max(3, len(rows) + 2)
    _aplicar_vista_limpia(ws, max_col=len(labels), max_row=last_row, extra_cols=8, extra_rows=12)
    _proteger_hoja(ws)


def _write_catalogo_partidas_sheet(wb: Workbook) -> None:
    from inspecciones.models import PartidaCatalogo

    name = "Catalogo_partidas"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    _set_tab_color(ws, TAB_REF)
    ws["A1"] = (
        "SOLO CONSULTA — copie el «codigo» a la pestaña Metrados (columna codigo_partida). "
        "No edite esta hoja salvo que el administrador actualice el catálogo."
    )
    ws["A1"].font = Font(name="Calibri", size=9, italic=True, color="455A64")
    ws["A1"].fill = PatternFill("solid", fgColor="ECEFF1")
    ws.merge_cells("A1:H1")
    headers = [
        "codigo",
        "grupo",
        "titulo",
        "unidad_default",
        "precio_unitario",
        "moneda",
        "aplica_decisiones",
        "descripcion",
    ]
    for col_i, h in enumerate(headers, start=1):
        cell = ws.cell(2, col_i, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="00247D")
    row_i = 3
    for p in PartidaCatalogo.objects.filter(activo=True).order_by("orden", "codigo"):
        vals = [
            p.codigo,
            p.grupo,
            p.titulo,
            p.unidad_default,
            float(p.precio_unitario) if p.precio_unitario is not None else "",
            p.moneda,
            p.aplica_decisiones,
            p.descripcion,
        ]
        for col_i, val in enumerate(vals, start=1):
            ws.cell(row_i, col_i, val)
        row_i += 1
    for i, w in enumerate([16, 14, 42, 10, 14, 8, 14, 36], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"
    _proteger_hoja(ws, solo_consulta=True)


def _write_metrados_sheet(wb: Workbook, caso: CasoRojo) -> None:
    name = "Metrados"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    _set_tab_color(ws, TAB_METRADOS)

    ws["A1"] = (
        "PESTAÑA PROTEGIDA — edite columnas ámbar/blanco. "
        "hab_id bloqueado. id_pln01 ata la línea al plano PLN-01 (p. ej. PB-C6). "
        "tipo_apuntamiento: preventivo | trabajo | ambos | na. "
        "codigo_partida = desplegable. Al cargar se reemplazan líneas de este hab_id."
    )
    ws["A1"].font = Font(name="Calibri", size=9, italic=True, color="5D4037")
    ws["A1"].fill = PatternFill("solid", fgColor="FFF8E1")
    ws.merge_cells("A1:N1")
    ws.row_dimensions[1].height = 48

    headers = [
        "hab_id",
        "orden",
        "codigo_partida",
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
    ]
    hints = [
        "ID del caso (no cambiar)",
        "1, 2, 3…",
        "DESPLEGABLE: APUNT_PREV, INY_FISURA…",
        "Lista cerrada",
        "ID PLN-01: PB-C6 / PB-V(A-B)·eje6",
        "PB, P1… (opcional)",
        "TEXTO LIBRE: torre / zona",
        "preventivo | trabajo | ambos | na",
        "Número",
        "Lista cerrada",
        "A / B / C",
        "Lista cerrada",
        "Alta / Media / Estimada",
        "TEXTO LIBRE (opcional)",
    ]
    for col_i, h in enumerate(headers, start=1):
        cell = ws.cell(2, col_i, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="F57F17")
    for col_i, hint in enumerate(hints, start=1):
        cell = ws.cell(3, col_i, hint)
        cell.font = Font(name="Calibri", size=8, italic=True, color="5D4037")
        cell.fill = PatternFill("solid", fgColor="FFFDE7")

    lineas = list(caso.lineas_metrado.select_related("partida").order_by("orden", "id"))
    row_i = 4
    list_cols = getattr(wb, "_cpeh_list_cols", None)
    if not list_cols:
        list_cols = {k: i + 1 for i, k in enumerate(LISTAS.keys())}

    def _append_linea(vals: list) -> None:
        nonlocal row_i
        # Cerrados (listas): 3 codigo, 4 elemento, 8 tipo_apunt, 10 und, 11 sev, 12 acc, 13 conf
        closed = {3, 4, 8, 10, 11, 12, 13}
        free = {5, 6, 7, 9, 14}  # id_pln01, piso, ubicacion, cantidad, nota
        for col_i, val in enumerate(vals, start=1):
            c = ws.cell(row_i, col_i, val)
            if col_i in closed:
                c.fill = PatternFill("solid", fgColor="FFF2CC")
            elif col_i in free:
                c.fill = PatternFill("solid", fgColor="FFFFFF")
            if col_i >= 2:
                _unlock_cell(c)
        if "codigo_partida" in list_cols and getattr(wb, "_cpeh_n_partidas", 0):
            col_letter = get_column_letter(list_cols["codigo_partida"])
            nvals = wb._cpeh_n_partidas
            formula = f"Listas_desplegables!${col_letter}$2:${col_letter}${nvals + 1}"
            ws.add_data_validation(_dv(formula, f"C{row_i}"))
        for lista_key, col_idx in (
            ("elemento_metrado", 4),
            ("tipo_apuntamiento", 8),
            ("unidad_metrado", 10),
            ("abc", 11),
            ("accion_metrado", 12),
            ("confianza_metrado", 13),
        ):
            if lista_key not in list_cols:
                continue
            col_letter = get_column_letter(list_cols[lista_key])
            nvals = len(LISTAS[lista_key])
            formula = f"Listas_desplegables!${col_letter}$2:${col_letter}${nvals + 1}"
            ws.add_data_validation(_dv(formula, f"{get_column_letter(col_idx)}{row_i}"))
        row_i += 1

    empty14 = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    if lineas:
        for ln in lineas:
            _append_linea(
                [
                    caso.hab_id,
                    ln.orden,
                    ln.codigo_partida or (ln.partida.codigo if ln.partida_id else ""),
                    ln.elemento,
                    ln.id_pln01 or "",
                    ln.piso_pln or "",
                    ln.ubicacion,
                    ln.tipo_apuntamiento or "na",
                    float(ln.cantidad) if ln.cantidad is not None else "",
                    ln.unidad,
                    ln.severidad,
                    ln.accion,
                    ln.confianza,
                    ln.nota,
                ]
            )
        next_orden = (lineas[-1].orden or len(lineas)) + 1
    else:
        for i in range(1, 9):
            row = [
                caso.hab_id,
                i,
                "",
                "Pendiente",
                "",
                "",
                "",
                "na",
                "",
                "Pendiente",
                "Pendiente",
                "Pendiente",
                "Pendiente",
                "",
            ]
            _append_linea(row)
        next_orden = 9

    for i in range(METRADOS_FILAS_EXTRA):
        row = [caso.hab_id, next_orden + i] + [""] * 12
        _append_linea(row)

    row_i += 1
    ws.cell(
        row_i,
        1,
        "Ejemplo D2/M1: APUNT_PREV o APUNT_COL (id_pln01=PB-C6) + REP_COL_LOCAL + INY_FISURA + FAC_MAMPOST. "
        "Códigos = desplegable (col. C). Ubicación/nota = criterio del ingeniero.",
    )
    ws.cell(row_i, 1).font = Font(name="Calibri", size=8, italic=True, color="666666")
    ws.merge_cells(start_row=row_i, start_column=1, end_row=row_i, end_column=11)

    for i, w in enumerate([10, 8, 18, 16, 20, 10, 10, 12, 18, 12, 28], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"
    _aplicar_vista_limpia(ws, max_col=11, max_row=max(row_i, 16))
    _proteger_hoja(ws)


def _write_catalogo_procedimientos_sheet(wb: Workbook) -> None:
    from inspecciones.catalogo_procedimientos import (
        asegurar_procedimientos_catalogo,
        listar_procedimientos_ayuda,
    )

    try:
        asegurar_procedimientos_catalogo()
    except Exception:
        pass

    name = "Catalogo_procedimientos"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    _set_tab_color(ws, TAB_REF)
    ws["A1"] = (
        "SOLO CONSULTA — catálogo VIG/COL/MAM. "
        "Marque Sí/No en la pestaña «Procedimientos_sel» (no invente códigos de partidas aquí)."
    )
    ws["A1"].font = Font(name="Calibri", size=9, italic=True, color="455A64")
    ws["A1"].fill = PatternFill("solid", fgColor="ECEFF1")
    ws.merge_cells("A1:D1")
    headers = ["codigo", "categoria", "titulo", "descripcion"]
    for col_i, h in enumerate(headers, start=1):
        cell = ws.cell(2, col_i, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="00247D")
    row_i = 3
    for p in listar_procedimientos_ayuda():
        for col_i, val in enumerate(
            [p["codigo"], p["categoria"], p["titulo"], p.get("descripcion", "")],
            start=1,
        ):
            ws.cell(row_i, col_i, val)
        row_i += 1
    for i, w in enumerate([12, 10, 42, 48], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"
    _proteger_hoja(ws, solo_consulta=True)


def _write_procedimientos_sel_sheet(wb: Workbook, caso: CasoRojo) -> None:
    """Pestaña Sí/No por código de procedimiento → se importa a proc_codigos."""
    import re

    from inspecciones.catalogo_procedimientos import (
        asegurar_procedimientos_catalogo,
        listar_procedimientos_ayuda,
    )

    try:
        asegurar_procedimientos_catalogo()
    except Exception:
        pass

    name = "Procedimientos_sel"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    _set_tab_color(ws, TAB_RELLENAR)
    ws["A1"] = (
        "PESTAÑA PROTEGIDA — solo edite la columna «seleccionar» (Sí/No). "
        "Código/categoría/título están bloqueados. Al cargar se actualiza «Procedimientos seleccionados». "
        "Texto libre adicional → Notas en la pestaña verde del informe."
    )
    ws["A1"].font = Font(name="Calibri", size=9, italic=True, color="1B5E20")
    ws["A1"].fill = PatternFill("solid", fgColor="E8F5E9")
    ws.merge_cells("A1:D1")
    ws.row_dimensions[1].height = 36

    for col_i, h in enumerate(["codigo", "categoria", "titulo", "seleccionar"], start=1):
        cell = ws.cell(2, col_i, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2E7D32")

    selected = set()
    raw = (caso.proc_codigos or "").upper()
    for part in re.split(r"[,;\n]+", raw):
        p = part.strip()
        if p:
            selected.add(p)

    list_cols = getattr(wb, "_cpeh_list_cols", {})
    row_i = 3
    first_data_row = 3
    for p in listar_procedimientos_ayuda():
        ws.cell(row_i, 1, p["codigo"])
        ws.cell(row_i, 2, p["categoria"])
        ws.cell(row_i, 3, p["titulo"])
        sel = "Sí" if p["codigo"].upper() in selected else "No"
        c = ws.cell(row_i, 4, sel)
        c.fill = PatternFill("solid", fgColor="FFF2CC")
        _unlock_cell(c)
        row_i += 1
    last_data_row = row_i - 1
    if last_data_row >= first_data_row:
        ws.add_data_validation(_dv('"Sí,No"', f"D{first_data_row}:D{last_data_row}"))

    for i, w in enumerate([12, 10, 48, 14], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"
    _aplicar_vista_limpia(ws, max_col=4, max_row=max(row_i, 8))
    _proteger_hoja(ws)


def generar_excel_informe(caso: CasoRojo, user=None) -> bytes:
    """Un edificio — hoja vertical tipo informe ejecutivo."""
    wb = Workbook()
    data = caso_to_dict(caso, plantilla_visita=True)
    nombre = data.get("_nombre") or data.get("nombre_hab") or ""
    sheet = _sheet_name_safe(caso.hab_id, nombre)
    _write_portada(
        wb,
        f"Plantilla informe — ID {caso.hab_id}",
        PROGRAMA,
        [
            ("Edificio", f"{nombre} (ID Habitable {caso.hab_id})"),
            (
                "Uso",
                "Lea Portada → pestaña VERDE (visita, sin §11) → ÁMBAR Metrados → "
                "Procedimientos_sel (Sí/No) → cargue el archivo. "
                "Fotos, croquis y firmas (§11) solo en la ficha web.",
            ),
            (
                "Devolución",
                "Cargar Excel llenado. §11 Evidencia (fotos/croquis/firmas) no forma parte de este archivo.",
            ),
            ("Formato", f"Informe individual · plantilla {PLANTILLA_VERSION}"),
        ],
        pestanas_rellenar=[
            f"{sheet}  ← VERDE (informe de visita)",
            "Metrados  ← ÁMBAR (cantidades / códigos)",
            "Procedimientos_sel  ← VERDE (Sí/No)",
        ],
    )
    # Listas ocultas (desplegables); sin pestañas de catálogo para no saturar
    _add_list_sheet(wb)
    _write_informe_sheet(
        wb,
        sheet,
        data,
        estados_dropdown=estados_para_excel(caso, user),
    )
    _write_metrados_sheet(wb, caso)
    _write_procedimientos_sel_sheet(wb, caso)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generar_excel_informes_multiples(casos: Iterable[CasoRojo], user=None) -> bytes:
    """Varios edificios — una hoja vertical por caso en el mismo libro."""
    casos_list = list(casos)
    wb = Workbook()
    ids = ", ".join(str(c.hab_id) for c in casos_list[:8])
    if len(casos_list) > 8:
        ids += f" … (+{len(casos_list) - 8})"
    pestanas = []
    for caso in casos_list[:12]:
        data0 = caso_to_dict(caso, plantilla_visita=True)
        pestanas.append(f"{_sheet_name_safe(caso.hab_id, data0.get('_nombre') or '')}  ← VERDE")
    pestanas.append("Metrados  ← ÁMBAR (primer caso; preferible informe individual)")
    pestanas.append("Procedimientos_sel  ← catálogo Sí/No (primer caso)")
    _write_portada(
        wb,
        f"Plantillas informe — {len(casos_list)} caso(s)",
        PROGRAMA,
        [
            ("Casos incluidos", ids),
            ("Uso", "Una pestaña verde por edificio. Para metrados/procedimientos por ID use informe individual."),
            ("Devolución", "Cargue el libro en el sistema (menú Cargar Excel)."),
            ("Formato", f"Informe múltiple · {PLANTILLA_VERSION}"),
        ],
        pestanas_rellenar=pestanas,
    )
    _add_list_sheet(wb)
    for caso in casos_list:
        data = caso_to_dict(caso, plantilla_visita=True)
        nombre = data.get("_nombre") or ""
        sheet = _sheet_name_safe(caso.hab_id, nombre)
        _write_informe_sheet(
            wb,
            sheet,
            data,
            estados_dropdown=estados_para_excel(caso, user),
        )
    if casos_list:
        _write_metrados_sheet(wb, casos_list[0])
        _write_procedimientos_sel_sheet(wb, casos_list[0])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generar_excel_lote(casos: Iterable[CasoRojo]) -> bytes:
    """Varios edificios — una fila por caso."""
    casos_list = list(casos)
    rows = [caso_to_dict(c, plantilla_visita=True) for c in casos_list]
    wb = Workbook()
    _write_portada(
        wb,
        f"Plantilla lote — {len(casos_list)} caso(s)",
        PROGRAMA,
        [
            ("Formato", "Una fila por edificio en la pestaña VERDE «Lote_informes»."),
            ("Columnas", "Fila 1 = clave técnica · Fila 2 = etiqueta · Desde fila 3 = datos."),
            ("Precarga", "Celdas azules = precarga (validar). Amarillas = listas."),
            ("Devolución", "Cargue el lote en el sistema. §11 Evidencia (fotos/croquis/firmas) solo en la ficha web."),
        ],
        pestanas_rellenar=["Lote_informes  ← pestaña VERDE (una fila por edificio)"],
    )
    _add_list_sheet(wb)
    _write_lote_sheet(wb, rows)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def nombre_archivo_informe(caso: CasoRojo) -> str:
    slug = re.sub(r"[^\w.-]+", "_", (caso.nombre_conf or caso.nombre_hab or "caso")[:30])
    return f"informe-rojo-{caso.hab_id}-{slug}.xlsx"


def nombre_archivo_lote(n: int) -> str:
    return f"lote-informes-rojo-{n}-casos.xlsx"


def nombre_archivo_multinforme(n: int) -> str:
    return f"informes-rojo-{n}-pestanas.xlsx"
