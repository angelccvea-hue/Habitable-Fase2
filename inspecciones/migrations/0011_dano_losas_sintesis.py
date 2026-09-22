from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0010_losas_dano_estructural"),
    ]

    operations = [
        migrations.AddField(
            model_name="casorojo",
            name="dano_losas",
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
                help_text="Si las losas están comprometidas en varios niveles, márquelo aquí y detalle en §6.",
                max_length=16,
                verbose_name="Daño losas (síntesis)",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="dano_vigas",
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
                verbose_name="Daño vigas (síntesis)",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="riesgo_fachada",
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
                verbose_name="Riesgo fachada (síntesis)",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="col_nivel",
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
                verbose_name="Columnas — nivel A/B/C",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="vig_nivel",
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
                verbose_name="Vigas — nivel A/B/C",
            ),
        ),
        migrations.AlterField(
            model_name="casorojo",
            name="mur_nivel",
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
                verbose_name="Muros/pantallas — nivel A/B/C",
            ),
        ),
        migrations.AlterField(
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
                verbose_name="Losas — nivel A/B/C",
            ),
        ),
    ]
