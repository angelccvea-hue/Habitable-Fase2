# Generated manually for HistorialDetallado

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inspecciones", "0013_credencial_emitida"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistorialDetallado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "resumen",
                    models.CharField(
                        help_text="Nota corta del cambio (p. ej. «Actualizó dictamen y metrados»).",
                        max_length=255,
                        verbose_name="Qué se hizo (breve)",
                    ),
                ),
                (
                    "detalle",
                    models.TextField(
                        blank=True,
                        help_text="Campos tocados, valores anterior → nuevo, adjuntos, etc.",
                        verbose_name="Detalle",
                    ),
                ),
                (
                    "origen",
                    models.CharField(
                        blank=True,
                        default="ficha",
                        help_text="ficha · accion_estado · excel · masivo · sistema",
                        max_length=32,
                        verbose_name="Origen",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Cuándo")),
                (
                    "caso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial_detallado",
                        to="inspecciones.casorojo",
                        verbose_name="Caso ROJO",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="historial_detallado_casos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial detallado",
                "verbose_name_plural": "Historial detallado",
                "ordering": ["-created_at"],
            },
        ),
    ]
