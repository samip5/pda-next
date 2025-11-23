from django.apps import AppConfig

class ActivityConfig(AppConfig):
    name = "apps.api.activity"
    label = "api_activity"
    verbose_name = "Activity Logs"
    default_auto_field = "django.db.models.BigAutoField"
