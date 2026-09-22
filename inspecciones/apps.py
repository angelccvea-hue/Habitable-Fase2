from django.apps import AppConfig


class InspeccionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inspecciones"
    verbose_name = "Inspecciones Fase II"

    def ready(self) -> None:
        from inspecciones.admin_dashboard import patch_admin_index

        patch_admin_index()
