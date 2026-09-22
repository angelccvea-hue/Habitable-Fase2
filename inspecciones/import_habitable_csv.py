# -*- coding: utf-8 -*-
"""Importación append-only de casos AMARILLO desde CSV Habitable.

No actualiza ni toca casos ya existentes (asignaciones, fichas, estados).
Solo crea hab_id que aún no estén en CasoRojo.
"""
from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator

from inspecciones.models import CasoRojo

BATCH = 400


def _txt(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_cert(value: Any) -> str:
    s = _txt(value)
    if s.startswith('="') and s.endswith('"'):
        s = s[2:-1]
    s = s.strip().strip('"').strip("=")
    return s


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _decimal_coord(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        d = Decimal(str(value).strip())
        if abs(d) > 180:
            return None
        return d
    except (InvalidOperation, ValueError):
        return None


def _fecha(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    # ISO con zona
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _riesgos(row: dict[str, Any]) -> str:
    partes = []
    for key, label in (
        ("riesgo_externo", "Ext"),
        ("riesgo_severo", "Sev"),
        ("riesgo_moderado", "Mod"),
        ("riesgo_componentes", "Comp"),
    ):
        v = _txt(row.get(key))
        if v:
            partes.append(f"{label} {v}")
    return " / ".join(partes)


def row_amarillo_to_caso(row: dict[str, Any]) -> CasoRojo | None:
    hab_id = _int(row.get("id"))
    if not hab_id:
        return None
    municipio = _txt(row.get("municipio"))
    parroquia = _txt(row.get("parroquia"))
    muni_parr = " / ".join(p for p in (municipio, parroquia) if p)
    lat = _decimal_coord(row.get("lat"))
    lng = _decimal_coord(row.get("lng"))
    gps_hab = f"{lat}, {lng}" if lat is not None and lng is not None else ""
    num_pisos = row.get("num_pisos")
    pisos_f1 = _txt(num_pisos) if num_pisos not in (None, "") else ""

    return CasoRojo(
        hab_id=hab_id,
        certificado=_clean_cert(row.get("certificado")),
        nombre_hab=_txt(row.get("nombre_edificacion"))[:255],
        etiqueta_f1="AMARILLO",
        fecha_f1=_fecha(row.get("created_at")),
        inspector_f1=_txt(row.get("inspector_nombre"))[:255],
        direccion_hab=_txt(row.get("direccion"))[:500],
        muni_parr=muni_parr[:255],
        pisos_f1=pisos_f1[:64],
        riesgos_f1=_riesgos(row)[:128],
        colapso_f1=_txt(row.get("ext_colapso_estructura"))[:16],
        piso_crit_f1=_txt(row.get("piso_critico"))[:255],
        acciones_f1=_txt(row.get("acc_medidas"))[:255],
        obs_f1=_txt(row.get("observaciones")),
        gps_hab=gps_hab[:64],
        lat=lat,
        lng=lng,
        score=None,
        banda="AMARILLO",
        puestos="",
        score_detalle="",
        prob_rel="",
        uso=_txt(row.get("uso"))[:128],
    )


def iter_csv_amarillo(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            et = _txt(row.get("etiqueta")).upper()
            if et != "AMARILLO":
                continue
            yield row


def importar_amarillos_solo_nuevos(
    path: Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict[str, int]:
    """
    Crea únicamente casos AMARILLO cuyo hab_id no exista.
    Nunca hace UPDATE de filas existentes.
    """
    stats = {
        "leidas_amarillo": 0,
        "ya_existian": 0,
        "creadas": 0,
        "errores": 0,
        "omitidas_sin_id": 0,
    }
    existentes = set(CasoRojo.objects.values_list("hab_id", flat=True))
    batch: list[CasoRojo] = []

    def flush() -> None:
        nonlocal batch
        if not batch:
            return
        if dry_run:
            stats["creadas"] += len(batch)
            batch = []
            return
        CasoRojo.objects.bulk_create(batch, ignore_conflicts=True)
        stats["creadas"] += len(batch)
        batch = []

    for row in iter_csv_amarillo(path):
        stats["leidas_amarillo"] += 1
        if limit is not None and stats["creadas"] + len(batch) >= limit:
            break
        hab_id = _int(row.get("id"))
        if not hab_id:
            stats["omitidas_sin_id"] += 1
            continue
        if hab_id in existentes:
            stats["ya_existian"] += 1
            continue
        try:
            obj = row_amarillo_to_caso(row)
            if obj is None:
                stats["omitidas_sin_id"] += 1
                continue
        except Exception:
            stats["errores"] += 1
            continue
        existentes.add(hab_id)  # evitar dup en mismo CSV
        batch.append(obj)
        if len(batch) >= BATCH:
            flush()

    flush()
    return stats
