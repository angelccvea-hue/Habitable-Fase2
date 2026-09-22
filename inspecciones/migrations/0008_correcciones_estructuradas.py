# Generated manually for corr_* campos de validación precarga

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0007_coordinador_asignado"),
    ]

    operations = [
        migrations.AddField(
            model_name="casorojo",
            name="corr_nombre",
            field=models.CharField(
                blank=True,
                help_text="Si corrige edificio: reemplaza el nombre Habitable (y el confirmado si está vacío).",
                max_length=255,
                verbose_name="Nombre correcto",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_direccion",
            field=models.CharField(
                blank=True,
                help_text="Reemplaza la dirección de precarga al guardar.",
                max_length=500,
                verbose_name="Dirección correcta",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_muni_parr",
            field=models.CharField(
                blank=True,
                help_text="Reemplaza municipio/parroquia de precarga al guardar.",
                max_length=255,
                verbose_name="Municipio / parroquia correctos",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_etiqueta",
            field=models.CharField(
                blank=True,
                help_text="Ej. ROJO. Reemplaza etiqueta_f1 al guardar.",
                max_length=20,
                verbose_name="Etiqueta correcta (Fase 1)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_pisos",
            field=models.CharField(
                blank=True,
                help_text="Ej. 10 / 2. Reemplaza pisos_f1 (y pisos_conf si vacío).",
                max_length=64,
                verbose_name="Pisos / sótanos correctos",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_gps",
            field=models.CharField(
                blank=True,
                help_text="Reemplaza gps_hab al guardar. El GPS de visita 2 se captura aparte.",
                max_length=64,
                verbose_name="GPS correcto (Habitable)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_score",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Solo si el ranking/score estaba mal. Reemplaza score al guardar.",
                null=True,
                verbose_name="Score correcto (0–100)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="corr_banda",
            field=models.CharField(
                blank=True,
                help_text="Reemplaza banda de prioridad al guardar.",
                max_length=32,
                verbose_name="Banda correcta",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="correcciones",
            field=models.TextField(
                blank=True,
                help_text="Opcional si ya llenó los campos «… correcto». Use esto para matices o varios edificios.",
                verbose_name="Nota adicional de corrección",
            ),
        ),
    ]
