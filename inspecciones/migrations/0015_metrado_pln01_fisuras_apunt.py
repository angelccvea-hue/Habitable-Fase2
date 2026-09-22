# Generated manually for MET-01 / PLN-01 linkage + fisuras + apuntamiento post-sísmico

from django.db import migrations, models


def seed_partidas_ampliadas(apps, schema_editor):
    from inspecciones.partidas_catalogo import PARTIDAS_SEMILLA

    PartidaCatalogo = apps.get_model("inspecciones", "PartidaCatalogo")
    for codigo, grupo, titulo, unidad, aplica, orden, desc in PARTIDAS_SEMILLA:
        PartidaCatalogo.objects.update_or_create(
            codigo=codigo,
            defaults={
                "grupo": grupo.value if hasattr(grupo, "value") else grupo,
                "titulo": titulo,
                "unidad_default": unidad.value if hasattr(unidad, "value") else unidad,
                "aplica_decisiones": aplica,
                "orden": orden,
                "descripcion": desc,
                "activo": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0014_historial_detallado"),
    ]

    operations = [
        migrations.AddField(
            model_name="lineametado",
            name="id_pln01",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Identificador del plano de inspección (p. ej. PB-C6, PB-V(A-B)·eje6, PB-M·ejeA·entre2-3).",
                max_length=64,
                verbose_name="ID elemento PLN-01",
            ),
        ),
        migrations.AddField(
            model_name="lineametado",
            name="piso_pln",
            field=models.CharField(
                blank=True,
                help_text="PB, P1, P2… alineado al título del plano de ese piso.",
                max_length=16,
                verbose_name="Piso (PLN-01)",
            ),
        ),
        migrations.AddField(
            model_name="lineametado",
            name="tipo_apuntamiento",
            field=models.CharField(
                blank=True,
                choices=[
                    ("preventivo", "Preventivo (estabilización post-sísmica)"),
                    ("trabajo", "De trabajo (durante la intervención)"),
                    ("ambos", "Preventivo + trabajo"),
                    ("na", "No aplica"),
                ],
                default="na",
                help_text="Obligatorio sentido post-sísmico cuando la partida es APUNT_*.",
                max_length=16,
                verbose_name="Tipo de apuntamiento",
            ),
        ),
        migrations.AlterField(
            model_name="lineametado",
            name="ubicacion",
            field=models.CharField(
                blank=True,
                help_text="Texto libre de apoyo; preferir también id_pln01 según PLN-01.",
                max_length=128,
                verbose_name="Ubicación (piso / eje / torre)",
            ),
        ),
        migrations.AlterField(
            model_name="partidacatalogo",
            name="grupo",
            field=models.CharField(
                choices=[
                    ("APUNTAMIENTO", "Apuntamiento / seguridad"),
                    ("REPARACION", "Reparación / refuerzo"),
                    ("FISURAS", "Fisuras / grietas"),
                    ("DEMOLICION", "Demolición"),
                    ("ESCOMBROS", "Escombros / retiro"),
                    ("ESTUDIOS", "Estudios / complementos (D1)"),
                    ("FACHADA", "Fachada / no estructural"),
                    ("MOVILIZACION", "Movilización / logística"),
                    ("OTRO", "Otro"),
                ],
                default="OTRO",
                max_length=16,
            ),
        ),
        migrations.RunPython(seed_partidas_ampliadas, migrations.RunPython.noop),
    ]
