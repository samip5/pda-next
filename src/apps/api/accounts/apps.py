from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = "apps.api.accounts"
    label = "api_accounts"
    verbose_name = "API Accounts"
    default_auto_field = "django.db.models.BigAutoField"
