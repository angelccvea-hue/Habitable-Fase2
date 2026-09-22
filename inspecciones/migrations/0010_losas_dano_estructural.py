# Generated manually for Losas / mur_evidencia in §6 daño estructural

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0009_cuantificacion_metrados"),
    ]

    operations = [
        migrations.AddField(
            model_name="casorojo",
            name="mur_evidencia",
            field=models.TextField(
                blank=True,
                verbose_name="Muros/pantallas — ubicación / evidencia",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="los_mec",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Losas — mecanismo",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="los_nivel",
            field=models.CharField(
                blank=True,
                choices=[
                    ("A", "A"),
                    ("B", "B"),
                    ("C", "C"),
                    ("No observable", "No observable"),
                    ("Pendiente", "Pendiente"),
                ],
                default="Pendiente",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="los_evidencia",
            field=models.TextField(
                blank=True,
                help_text="Indique pisos/niveles afectados (ej. losa entrepiso 3–5, zona central).",
                verbose_name="Losas — ubicación / evidencia",
            ),
        ),
    ]
