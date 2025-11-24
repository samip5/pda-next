from django.apps import AppConfig


class APIConfig(AppConfig):
    name = "apps.api"
    label = "api"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        try:
            from apps.api.authconfig.helpers import apply_db_settings_prefer_env

            apply_db_settings_prefer_env()
        except Exception:
            # ignore errors during migration/collectstatic phases
            pass
