# -*- coding: utf-8 -*-
"""Importa casos AMARILLO desde CSV Habitable — solo altas, sin tocar existentes."""
from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from inspecciones.import_habitable_csv import importar_amarillos_solo_nuevos


class Command(BaseCommand):
    help = (
        "Amplía el universo Fase II con casos AMARILLO del CSV Habitable. "
        "Solo crea hab_id nuevos; no modifica ni reasigna casos existentes."
    )

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, required=True, help="Ruta al CSV Habitable")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        path = Path(options["csv"])
        if not path.is_file():
            raise CommandError(f"CSV no encontrado: {path}")
        stats = importar_amarillos_solo_nuevos(
            path,
            dry_run=options["dry_run"],
            limit=options["limit"],
        )
        modo = "SIMULACIÓN" if options["dry_run"] else "IMPORTADO"
        self.stdout.write(
            self.style.SUCCESS(
                f"{modo} amarillos — leídas={stats['leidas_amarillo']} "
                f"creadas={stats['creadas']} ya_existían={stats['ya_existian']} "
                f"sin_id={stats['omitidas_sin_id']} errores={stats['errores']}"
            )
        )
