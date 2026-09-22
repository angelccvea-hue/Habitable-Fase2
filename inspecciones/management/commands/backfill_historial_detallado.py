# -*- coding: utf-8 -*-
"""Rellena Historial detallado desde historial de estados / log admin."""
from django.core.management.base import BaseCommand

from inspecciones.historial_detalle import backfill_historial_detallado


class Command(BaseCommand):
    help = (
        "Crea entradas de Historial detallado a partir del historial de estados "
        "(y opcionalmente del log de admin) para casos antiguos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--hab-id",
            type=int,
            default=None,
            help="Solo un ID Habitable (p. ej. 4026).",
        )
        parser.add_argument(
            "--sin-log",
            action="store_true",
            help="No incluir LogEntry del admin (solo historial de estados).",
        )

    def handle(self, *args, **options):
        stats = backfill_historial_detallado(
            hab_id=options.get("hab_id"),
            incluir_log=not options.get("sin_log"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"OK backfill: estados={stats['estados']} "
                f"notas_estado={stats['notas_estado']} "
                f"log={stats['log']} casos={stats['casos']}"
            )
        )
