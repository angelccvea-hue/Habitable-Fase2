# Generated manually for EquipoBrigada + seed etiquetas.

from django.db import migrations, models


EQUIPOS_SEED = [
    (1, "Ataguia"),
    (2, "Ritchen"),
    (3, "Onix"),
    (4, ""),
    (5, ""),
    (6, ""),
    (7, ""),
    (8, ""),
]


def seed_equipos(apps, schema_editor):
    EquipoBrigada = apps.get_model("inspecciones", "EquipoBrigada")
    for num, nombre in EQUIPOS_SEED:
        EquipoBrigada.objects.update_or_create(
            numero=num,
            defaults={"nombre": nombre or f"Equipo {num}", "activo": True},
        )
    # Si el seed dejó "Equipo N" como nombre vacío útil: usar nombre solo si hay etiqueta
    for num, nombre in EQUIPOS_SEED:
        if nombre:
            EquipoBrigada.objects.filter(numero=num).update(nombre=nombre)


def unseed_equipos(apps, schema_editor):
    EquipoBrigada = apps.get_model("inspecciones", "EquipoBrigada")
    EquipoBrigada.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0011_dano_losas_sintesis"),
    ]

    operations = [
        migrations.CreateModel(
            name="EquipoBrigada",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "numero",
                    models.PositiveSmallIntegerField(
                        db_index=True,
                        help_text="Coincide con coord.equipoN / ing.equipoN en el username.",
                        unique=True,
                        verbose_name="N.º de equipo",
                    ),
                ),
                (
                    "nombre",
                    models.CharField(
                        help_text="Ej. Ataguia, Ritchen, Onix.",
                        max_length=80,
                        verbose_name="Nombre / etiqueta",
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("notas", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Equipo / brigada",
                "verbose_name_plural": "Equipos / brigadas",
                "ordering": ["numero"],
            },
        ),
        migrations.RunPython(seed_equipos, unseed_equipos),
    ]
