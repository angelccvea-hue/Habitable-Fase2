# Croquis adjunto + índice
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inspecciones", "0005_d1_complementos_d1_d4"),
    ]

    operations = [
        migrations.CreateModel(
            name="CroquisAdjunto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "archivo",
                    models.FileField(
                        help_text="Imagen (JPG/PNG/WEBP) o PDF del croquis / esquema estructural.",
                        upload_to="croquis/%Y/%m/",
                        verbose_name="Archivo croquis",
                    ),
                ),
                ("titulo", models.CharField(blank=True, max_length=255, verbose_name="Título / referencia")),
                ("notas", models.TextField(blank=True, verbose_name="Notas")),
                (
                    "nombre_archivo_origen",
                    models.CharField(blank=True, max_length=255, verbose_name="Nombre archivo origen"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "caso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="croquis",
                        to="inspecciones.casorojo",
                        verbose_name="Caso ROJO",
                    ),
                ),
                (
                    "subido_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="croquis_subidos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Croquis adjunto",
                "verbose_name_plural": "Croquis adjuntos",
                "ordering": ["-created_at"],
            },
        ),
    ]
