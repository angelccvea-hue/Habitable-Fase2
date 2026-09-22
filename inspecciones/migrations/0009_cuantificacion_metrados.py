# Generated manually — cuantificación / metrados / catálogo partidas

import django.db.models.deletion
from django.db import migrations, models


def seed_partidas(apps, schema_editor):
    PartidaCatalogo = apps.get_model("inspecciones", "PartidaCatalogo")
    from inspecciones.partidas_catalogo import PARTIDAS_SEMILLA

    for codigo, grupo, titulo, unidad, aplica, orden, desc in PARTIDAS_SEMILLA:
        PartidaCatalogo.objects.update_or_create(
            codigo=codigo,
            defaults={
                "grupo": grupo,
                "titulo": titulo,
                "unidad_default": unidad,
                "aplica_decisiones": aplica,
                "orden": orden,
                "descripcion": desc,
                "activo": True,
            },
        )


def unseed_partidas(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inspecciones", "0008_correcciones_estructuradas"),
    ]

    operations = [
        migrations.AddField(
            model_name="casorojo",
            name="area_aprox_m2",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Estimación para costo grueso y anteproyecto.",
                max_digits=12,
                null=True,
                verbose_name="Área aproximada construida (m²)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="n_viviendas",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="N.º viviendas / unidades"
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="vol_escombros_m3",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Relevante sobre todo en D3/D4.",
                max_digits=12,
                null=True,
                verbose_name="Volumen estimado escombros (m³)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="m_fachada_riesgo",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name="Fachada en riesgo (m lineales o m²)",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="niveles_intervenir",
            field=models.CharField(
                blank=True,
                help_text="Ej. 1–4, sótano+PB, todos.",
                max_length=64,
                verbose_name="Niveles a intervenir",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="pct_estructura_intervenir",
            field=models.CharField(
                blank=True,
                choices=[
                    ("No observable", "No observable"),
                    ("<10%", "<10%"),
                    ("10–30%", "10–30%"),
                    (">30%", ">30%"),
                    (">50%", ">50%"),
                    ("Pendiente", "Pendiente"),
                ],
                default="Pendiente",
                max_length=32,
                verbose_name="% estructura a intervenir",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="metrado_confianza",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Alta", "Alta"),
                    ("Media", "Media"),
                    ("Estimada", "Estimada"),
                    ("Pendiente", "Pendiente"),
                ],
                default="Pendiente",
                max_length=16,
                verbose_name="Confianza global del metrado",
            ),
        ),
        migrations.AddField(
            model_name="casorojo",
            name="metrado_notas",
            field=models.TextField(
                blank=True,
                help_text="Supuestos del levantamiento; no sustituye las líneas de metrado.",
                verbose_name="Notas de cuantificación",
            ),
        ),
        migrations.CreateModel(
            name="PartidaCatalogo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_index=True, max_length=32, unique=True, verbose_name="Código partida")),
                (
                    "grupo",
                    models.CharField(
                        choices=[
                            ("APUNTAMIENTO", "Apuntamiento / seguridad"),
                            ("REPARACION", "Reparación / refuerzo"),
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
                ("titulo", models.CharField(max_length=255)),
                ("descripcion", models.TextField(blank=True)),
                (
                    "unidad_default",
                    models.CharField(
                        choices=[
                            ("m", "m (metro lineal)"),
                            ("m²", "m²"),
                            ("m³", "m³"),
                            ("und", "und (unidad)"),
                            ("kg", "kg"),
                            ("m.l.", "m.l."),
                            ("glb", "glb (global / lote)"),
                            ("piso", "piso(s)"),
                            ("Pendiente", "Pendiente"),
                        ],
                        default="und",
                        max_length=16,
                    ),
                ),
                (
                    "precio_unitario",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Vacío por ahora; cuando se cargue, habilita costo estimado = cantidad × PU.",
                        max_digits=14,
                        null=True,
                        verbose_name="Precio unitario (opcional)",
                    ),
                ),
                ("moneda", models.CharField(blank=True, default="USD", max_length=8)),
                (
                    "aplica_decisiones",
                    models.CharField(
                        blank=True,
                        help_text="Ej. D2,D3 o D1,D2 (vacío = todas).",
                        max_length=64,
                        verbose_name="Aplica a decisiones",
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("orden", models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                "verbose_name": "Partida de metrado (catálogo)",
                "verbose_name_plural": "Catálogo de partidas (metrados / costos)",
                "ordering": ["orden", "grupo", "codigo"],
            },
        ),
        migrations.CreateModel(
            name="LineaMetrado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("orden", models.PositiveSmallIntegerField(default=1)),
                (
                    "codigo_partida",
                    models.CharField(
                        blank=True,
                        help_text="Se rellena desde el catálogo; editable para Excel.",
                        max_length=32,
                        verbose_name="Código partida",
                    ),
                ),
                (
                    "elemento",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Columna", "Columna"),
                            ("Viga", "Viga"),
                            ("Muro / pantalla", "Muro / pantalla"),
                            ("Losa", "Losa"),
                            ("Escalera", "Escalera"),
                            ("Fachada", "Fachada"),
                            ("Sótano / semisótano", "Sótano / semisótano"),
                            ("Cimentación", "Cimentación"),
                            ("Edificio completo", "Edificio completo"),
                            ("Entorno / vía", "Entorno / vía"),
                            ("Otro", "Otro"),
                            ("Pendiente", "Pendiente"),
                        ],
                        default="Pendiente",
                        max_length=32,
                    ),
                ),
                ("ubicacion", models.CharField(blank=True, max_length=128, verbose_name="Ubicación (piso / eje / torre)")),
                ("cantidad", models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True)),
                (
                    "unidad",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("m", "m (metro lineal)"),
                            ("m²", "m²"),
                            ("m³", "m³"),
                            ("und", "und (unidad)"),
                            ("kg", "kg"),
                            ("m.l.", "m.l."),
                            ("glb", "glb (global / lote)"),
                            ("piso", "piso(s)"),
                            ("Pendiente", "Pendiente"),
                        ],
                        default="Pendiente",
                        max_length=16,
                    ),
                ),
                (
                    "severidad",
                    models.CharField(
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
                (
                    "accion",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Apuntalar / shoring", "Apuntalar / shoring"),
                            ("Reparar", "Reparar"),
                            ("Reforzar", "Reforzar"),
                            ("Demoler", "Demoler"),
                            ("Retirar / desmontar", "Retirar / desmontar"),
                            ("Acordonar / proteger", "Acordonar / proteger"),
                            ("Monitorear", "Monitorear"),
                            ("Estudio / ensayo", "Estudio / ensayo"),
                            ("Otro", "Otro"),
                            ("Pendiente", "Pendiente"),
                        ],
                        default="Pendiente",
                        max_length=32,
                    ),
                ),
                (
                    "confianza",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Alta", "Alta"),
                            ("Media", "Media"),
                            ("Estimada", "Estimada"),
                            ("Pendiente", "Pendiente"),
                        ],
                        default="Pendiente",
                        max_length=16,
                    ),
                ),
                ("nota", models.CharField(blank=True, max_length=500)),
                (
                    "caso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lineas_metrado",
                        to="inspecciones.casorojo",
                        verbose_name="Caso ROJO",
                    ),
                ),
                (
                    "partida",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lineas",
                        to="inspecciones.partidacatalogo",
                        verbose_name="Partida (catálogo)",
                    ),
                ),
            ],
            options={
                "verbose_name": "Línea de metrado",
                "verbose_name_plural": "Líneas de metrado",
                "ordering": ["orden", "id"],
            },
        ),
        migrations.RunPython(seed_partidas, unseed_partidas),
    ]
