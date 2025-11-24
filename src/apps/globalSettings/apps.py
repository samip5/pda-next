from django.apps import AppConfig
import logging

logger = logging.getLogger("pda")

class GlobalSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.globalSettings"

    def ready(self):
        """
        Load database settings when Django starts.
        This merges DB settings with the existing Pydantic config.
        """
        # Import here to avoid AppRegistryNotReady
        from django.conf import settings as django_settings
        from django.core.cache import cache
        from django.db import connection
        from .models import GlobalSetting
        try:
            if hasattr(django_settings, 'APP_SETTINGS'):
                app_settings = django_settings.APP_SETTINGS
                # Ensure table exists
                if 'global_settings' in connection.introspection.table_names():
                    db_settings = {}
                    for setting in GlobalSetting.objects.all():
                        val = setting.get_value()
                        db_settings[setting.key] = val
                        cache.set(f'global_setting_{setting.key}', val, None)
                    cache.set('all_global_settings', db_settings, None)
                    # Merge (env already applied; DB only overrides if attribute exists)
                    for key, value in db_settings.items():
                        if hasattr(app_settings, key):
                            setattr(app_settings, key, value)
                    logger.info(f"\u2713 Database settings loaded ({len(db_settings)})")
        except Exception as e:
            logger.error(f"Failed to load database settings: {e}")