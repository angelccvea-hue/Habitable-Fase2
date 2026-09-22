# Generated manually for CredencialEmitida.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inspecciones", "0012_equipo_brigada"),
    ]

    operations = [
        migrations.CreateModel(
            name="CredencialEmitida",
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
                    "password_plain",
                    models.CharField(max_length=128, verbose_name="Clave emitida"),
                ),
                ("emitida_en", models.DateTimeField(auto_now=True)),
                ("nota", models.CharField(blank=True, max_length=255)),
                (
                    "emitida_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="credenciales_emitidas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Emitida por",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credencial_emitida",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Credencial emitida",
                "verbose_name_plural": "Credenciales emitidas",
            },
        ),
    ]
