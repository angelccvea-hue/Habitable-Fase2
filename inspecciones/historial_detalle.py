# -*- coding: utf-8 -*-
"""Auditoría de cambios de CasoRojo → HistorialDetallado."""
from __future__ import annotations

from typing import Any

from django.db.models import Model
from django.utils import timezone

# Campos que no aportan a la narrativa del inspector/revisor
_SKIP = {
    "id",
    "hab_id",
    "created_at",
    "updated_at",
    "password",
}


def _fmt(val: Any, *, max_len: int = 120) -> str:
    if val is None:
        return "—"
    if hasattr(val, "pk") and not isinstance(val, (str, bytes)):
        # FK / User
        try:
            return str(val)
        except Exception:
            return f"#{getattr(val, 'pk', '?')}"
    s = str(val).strip()
    if not s:
        return "(vacío)"
    s = " ".join(s.split())
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def snapshot_caso(caso: Model) -> dict[str, Any]:
    """Valores actuales de campos escalares/FK del caso (para diff)."""
    data: dict[str, Any] = {}
    if not caso or not getattr(caso, "pk", None):
        return data
    for f in caso._meta.fields:
        name = f.name
        if name in _SKIP:
            continue
        if f.is_relation and f.many_to_many:
            continue
        try:
            if f.is_relation and f.many_to_one:
                data[name] = getattr(caso, f"{name}_id", None)
            else:
                data[name] = getattr(caso, name, None)
        except Exception:
            continue
    return data


def counts_adjuntos(caso) -> dict[str, int]:
    if not caso or not getattr(caso, "pk", None):
        return {"metrados": 0, "fotos": 0, "pdf": 0, "croquis": 0}
    return {
        "metrados": caso.lineas_metrado.count(),
        "fotos": caso.fotos.count(),
        "pdf": caso.informes_pdf.count(),
        "croquis": caso.croquis.count(),
    }


def _label(caso_model, field_name: str) -> str:
    try:
        return str(caso_model._meta.get_field(field_name).verbose_name)
    except Exception:
        return field_name


def diff_campos(caso_model, before: dict, after: dict, *, limite: int = 40) -> list[str]:
    lines: list[str] = []
    keys = sorted(set(before) | set(after))
    for name in keys:
        if name in _SKIP:
            continue
        a = before.get(name)
        b = after.get(name)
        if a == b:
            continue
        # Ambos vacíos
        if (a in (None, "")) and (b in (None, "")):
            continue
        lab = _label(caso_model, name)
        lines.append(f"• {lab}: {_fmt(a)} → {_fmt(b)}")
        if len(lines) >= limite:
            lines.append("• … (más cambios omitidos)")
            break
    return lines


def diff_counts(before: dict[str, int], after: dict[str, int]) -> list[str]:
    labels = {
        "metrados": "Líneas de metrado",
        "fotos": "Evidencias fotográficas",
        "pdf": "Informes PDF",
        "croquis": "Croquis",
    }
    out = []
    for k, lab in labels.items():
        a, b = before.get(k, 0), after.get(k, 0)
        if a != b:
            out.append(f"• {lab}: {a} → {b}")
    return out


def resumen_desde_diffs(cambios: list[str], *, estado_cambio: str | None = None) -> str:
    if estado_cambio:
        return estado_cambio
    if not cambios:
        return "Guardó la ficha (sin cambios de campos detectados)"
    # Extraer nombres cortos
    nombres = []
    for line in cambios[:4]:
        if ": " in line:
            nombres.append(line.split(":", 1)[0].lstrip("• ").strip())
    if len(cambios) == 1:
        return f"Actualizó {nombres[0]}" if nombres else "Actualizó 1 campo"
    if len(cambios) <= 3 and nombres:
        return "Actualizó " + ", ".join(nombres)
    return f"Actualizó {len(cambios)} campos del informe"


def registrar_historial_detallado(
    *,
    caso,
    usuario=None,
    resumen: str,
    detalle: str = "",
    origen: str = "ficha",
):
    from inspecciones.models import HistorialDetallado

    if not caso or not getattr(caso, "pk", None):
        return None
    resumen = (resumen or "Cambio registrado").strip()[:255]
    detalle = (detalle or "").strip()
    if not detalle:
        when = timezone.localtime().strftime("%d/%m/%Y %H:%M")
        who = str(usuario) if usuario else "sistema"
        detalle = f"Cuándo: {when}\nQuién: {who}\n{resumen}"
    return HistorialDetallado.objects.create(
        caso=caso,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        resumen=resumen,
        detalle=detalle,
        origen=(origen or "ficha")[:32],
    )


def registrar_guardado_ficha(
    *,
    caso,
    usuario,
    before: dict,
    before_counts: dict[str, int] | None = None,
    origen: str = "ficha",
    nota_extra: str = "",
):
    """Compara snapshot previo vs estado actual y crea entrada de historial detallado."""
    after = snapshot_caso(caso)
    cambios = diff_campos(type(caso), before, after)
    count_lines: list[str] = []
    if before_counts is not None:
        count_lines = diff_counts(before_counts, counts_adjuntos(caso))
    all_lines = cambios + count_lines
    if nota_extra:
        all_lines.append(f"• Nota: {nota_extra}")

    if not all_lines:
        # Re-guardado sin diferencias: no saturar el historial
        return None

    estado_txt = None
    if before.get("estado_2da") != after.get("estado_2da"):
        estado_txt = (
            f"Cambió estado: {_fmt(before.get('estado_2da'))} → {_fmt(after.get('estado_2da'))}"
        )

    resumen = resumen_desde_diffs(all_lines, estado_cambio=estado_txt)
    when = timezone.localtime().strftime("%d/%m/%Y %H:%M")
    who = str(usuario) if usuario else "sistema"
    cuerpo = [f"Cuándo: {when}", f"Quién: {who}", f"Resumen: {resumen}", ""]
    cuerpo.append("Cambios:")
    cuerpo.extend(all_lines)
    return registrar_historial_detallado(
        caso=caso,
        usuario=usuario,
        resumen=resumen,
        detalle="\n".join(cuerpo),
        origen=origen,
    )


def backfill_historial_detallado(*, hab_id: int | None = None, incluir_log: bool = True) -> dict:
    """
    Rellena HistorialDetallado a partir de HistorialEstado (y opcionalmente LogEntry)
    para casos que tienen transiciones pero la bitácora detallada quedó vacía
    (cambios anteriores al despliegue del historial detallado).
    """
    from datetime import timedelta

    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType

    from inspecciones.models import CasoRojo, HistorialDetallado, HistorialEstado

    stats = {"estados": 0, "notas_estado": 0, "log": 0, "casos": 0}

    he_qs = HistorialEstado.objects.select_related("caso", "usuario").order_by("id")
    if hab_id is not None:
        he_qs = he_qs.filter(caso__hab_id=hab_id)

    casos_tocados: set[int] = set()
    for he in he_qs.iterator(chunk_size=200):
        casos_tocados.add(he.caso_id)
        ref = f"ref:hestado:{he.pk}"
        if HistorialDetallado.objects.filter(caso_id=he.caso_id, detalle__contains=ref).exists():
            continue

        ant = (he.estado_anterior or "").strip() or "(sin estado previo)"
        nuevo = (he.estado_nuevo or "").strip() or "—"
        nota = (he.nota or "").strip()
        if not nota:
            nota = f"Cambio de estado: {ant} → {nuevo}"
            HistorialEstado.objects.filter(pk=he.pk).update(nota=nota[:500] if len(nota) > 500 else nota)
            # TextField has no max but keep reasonable
            stats["notas_estado"] += 1

        resumen = nota if len(nota) <= 255 else f"Cambió estado: {ant} → {nuevo}"
        when = timezone.localtime(he.created_at).strftime("%d/%m/%Y %H:%M") if he.created_at else "—"
        who = str(he.usuario) if he.usuario_id else "sistema"
        detalle = (
            f"Cuándo: {when}\n"
            f"Quién: {who}\n"
            f"Estado: {ant} → {nuevo}\n"
            f"Nota: {nota}\n"
            f"{ref}"
        )
        hd = HistorialDetallado.objects.create(
            caso_id=he.caso_id,
            usuario_id=he.usuario_id,
            resumen=resumen[:255],
            detalle=detalle,
            origen="backfill_estado",
        )
        if he.created_at:
            HistorialDetallado.objects.filter(pk=hd.pk).update(created_at=he.created_at)
        stats["estados"] += 1

    if incluir_log:
        ct = ContentType.objects.get_for_model(CasoRojo)
        log_qs = LogEntry.objects.filter(content_type=ct).select_related("user").order_by("id")
        if hab_id is not None:
            caso = CasoRojo.objects.filter(hab_id=hab_id).only("pk").first()
            if caso:
                log_qs = log_qs.filter(object_id=str(caso.pk))
            else:
                log_qs = log_qs.none()

        for entry in log_qs.iterator(chunk_size=200):
            ref = f"ref:logentry:{entry.pk}"
            try:
                caso_pk = int(entry.object_id)
            except (TypeError, ValueError):
                continue
            if hab_id is not None and caso_pk not in casos_tocados:
                # still allow log-only for that hab
                if not CasoRojo.objects.filter(pk=caso_pk, hab_id=hab_id).exists():
                    continue
            if HistorialDetallado.objects.filter(caso_id=caso_pk, detalle__contains=ref).exists():
                continue
            # Evitar duplicar si ya hay backfill_estado en ±2 min del mismo usuario
            # (el log de admin suele acompañar el cambio de estado)
            if entry.action_time and HistorialDetallado.objects.filter(
                caso_id=caso_pk,
                origen="backfill_estado",
                created_at__gte=entry.action_time - timedelta(minutes=2),
                created_at__lte=entry.action_time + timedelta(minutes=2),
            ).exists():
                # Aun así registrar si el change_message aporta detalle de campos
                msg = (entry.change_message or "").strip()
                if not msg or msg in ("[]", "Changed."):
                    continue

            accion = "Modificó"
            if entry.is_addition():
                accion = "Creó / dio de alta"
            elif entry.is_deletion():
                accion = "Eliminó"
            msg = (entry.change_message or "").strip() or "(sin detalle en el registro del sistema)"
            if len(msg) > 800:
                msg = msg[:799] + "…"
            resumen = f"{accion} el caso (registro admin)"
            when = (
                timezone.localtime(entry.action_time).strftime("%d/%m/%Y %H:%M")
                if entry.action_time
                else "—"
            )
            who = str(entry.user) if entry.user_id else "sistema"
            detalle = (
                f"Cuándo: {when}\n"
                f"Quién: {who}\n"
                f"Acción: {accion}\n"
                f"Detalle sistema: {msg}\n"
                f"{ref}"
            )
            hd = HistorialDetallado.objects.create(
                caso_id=caso_pk,
                usuario_id=entry.user_id,
                resumen=resumen[:255],
                detalle=detalle,
                origen="backfill_log",
            )
            if entry.action_time:
                HistorialDetallado.objects.filter(pk=hd.pk).update(created_at=entry.action_time)
            stats["log"] += 1
            casos_tocados.add(caso_pk)

    stats["casos"] = len(casos_tocados)
    return stats
