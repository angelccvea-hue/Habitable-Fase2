# Plantas de inspección multi-nivel + codigo_piso en croquis

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0015_metrado_pln01_fisuras_apunt"),
    ]

    operations = [
        migrations.AddField(
            model_name="croquisadjunto",
            name="codigo_piso",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="PB, P1, P2, SS1… — asocia el croquis a una planta del visor PLN-01.",
                max_length=16,
                verbose_name="Código de planta",
            ),
        ),
        migrations.CreateModel(
            name="PlantaInspeccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "codigo_piso",
                    models.CharField(
                        db_index=True,
                        help_text="PB, P1, P2, SS1… — prefijo de los id_pln01 de esta planta.",
                        max_length=16,
                        verbose_name="Código de planta",
                    ),
                ),
                (
                    "titulo",
                    models.CharField(
                        blank=True,
                        help_text="Ej. Planta baja · Torre A",
                        max_length=128,
                        verbose_name="Título",
                    ),
                ),
                ("orden", models.PositiveSmallIntegerField(default=1)),
                ("activa", models.BooleanField(default=True)),
                ("notas", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "caso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plantas_inspeccion",
                        to="inspecciones.casorojo",
                        verbose_name="Caso ROJO",
                    ),
                ),
                (
                    "croquis",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="plantas",
                        to="inspecciones.croquisadjunto",
                        verbose_name="Croquis asociado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Planta de inspección",
                "verbose_name_plural": "Plantas de inspección",
                "ordering": ["orden", "codigo_piso", "id"],
                "unique_together": {("caso", "codigo_piso")},
            },
        ),
        migrations.AlterModelOptions(
            name="croquisadjunto",
            options={
                "ordering": ["codigo_piso", "-created_at"],
                "verbose_name": "Croquis adjunto",
                "verbose_name_plural": "Croquis adjuntos",
            },
        ),
    ]
