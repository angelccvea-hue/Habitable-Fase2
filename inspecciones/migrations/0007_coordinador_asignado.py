# Coordinador asignado en cascada Admin → Coordinador → Ingeniero
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inspecciones", "0006_croquis_adjunto"),
    ]

    operations = [
        migrations.AddField(
            model_name="casorojo",
            name="coordinador_asignado",
            field=models.ForeignKey(
                blank=True,
                help_text="Administrador asigna el caso al coordinador; este a su vez asigna ingenieros.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="casos_coordinacion",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Coordinador asignado",
            ),
        ),
    ]
