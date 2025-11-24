from django.core.cache import cache
import logging

logger = logging.getLogger("pda")

def _get_app_settings():
    """Helper to get the AppSettings instance from config module"""
    try:
        # We need to get the actual AppSettings instance, not the settings submodule
        # Import config/__init__.py's namespace
        import config

        # Look through the module's __dict__ to find the AppSettings instance
        # We need to check __dict__ directly to avoid Python giving us the submodule
        if 'settings' in config.__dict__:
            settings_obj = config.__dict__['settings']
            # Verify it's a Pydantic model (not a module)
            if hasattr(settings_obj, '__fields__'):
                logger.debug(f"Found AppSettings instance at config.settings (type: {type(settings_obj)})")
                return settings_obj

        # Fallback: try app_settings
        if hasattr(config, 'app_settings') and hasattr(config.app_settings, '__fields__'):
            logger.debug("Found AppSettings instance at config.app_settings")
            return config.app_settings

        logger.error("Could not find AppSettings instance in config module")
        logger.error(f"config.__dict__ keys: {list(config.__dict__.keys())}")

    except ImportError as e:
        logger.error(f"Could not import config module: {e}")
    except Exception as e:
        logger.error(f"Error getting app settings: {e}")

    return None


def get_setting(key, default=None, use_cache=True):
    """
    Get a setting value. Checks in this order:
    1. Cache (if enabled)
    2. Database
    3. AppSettings object (from env/config file)
    4. Default value
    """
    from apps.globalSettings.models import GlobalSetting

    cache_key = f'global_setting_{key}'

    # Try cache first
    if use_cache:
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

    # Try database
    try:
        setting = GlobalSetting.objects.get(key=key)
        value = setting.get_value()

        if use_cache:
            cache.set(cache_key, value, None)

        return value
    except GlobalSetting.DoesNotExist:
        pass

    # Try AppSettings object (the instance from config module)
    app_settings = _get_app_settings()
    if app_settings and hasattr(app_settings, key):
        return getattr(app_settings, key)

    # Return default
    return default


def set_setting(key, value, setting_type='string', description=''):
    """
    Set a setting in the database.
    This will also update the AppSettings object if it has this field.
    """
    import json
    from apps.globalSettings.models import GlobalSetting

    if setting_type == 'json' and not isinstance(value, str):
        value = json.dumps(value)

    setting, created = GlobalSetting.objects.update_or_create(
        key=key,
        defaults={
            'value': str(value),
            'setting_type': setting_type,
            'description': description
        }
    )

    # Update AppSettings object if it exists
    app_settings = _get_app_settings()
    if app_settings and hasattr(app_settings, key):
        converted_value = setting.get_value()
        setattr(app_settings, key, converted_value)
        logger.info(f"Updated AppSettings.{key} = {converted_value}")

    return setting


def sync_env_settings_to_db():
    """
    Sync settings from AppSettings (env/config file) to database.
    Call this manually via management command to populate initial DB settings.
    """
    from apps.globalSettings.models import GlobalSetting

    # Get the AppSettings instance
    app_settings = _get_app_settings()

    if not app_settings:
        logger.error("Could not load AppSettings instance from config module")
        # Try to give more info about what we found
        try:
            import config
            logger.error(f"config module type: {type(config)}")
            logger.error(f"config module attributes: {dir(config)}")
            if hasattr(config, 'settings'):
                logger.error(f"config.settings type: {type(config.settings)}")
                logger.error(f"config.settings value: {config.settings}")
        except Exception as e:
            logger.error(f"Error inspecting config: {e}")
        return 0

    if not hasattr(app_settings, '__fields__'):
        logger.error(f"app_settings is not a Pydantic model instance. Type: {type(app_settings)}")
        logger.error(f"app_settings attributes: {dir(app_settings)}")
        return 0

    synced = 0

    # Define which fields should be synced to DB
    # Exclude internal/system fields
    exclude_fields = {'config', 'root_path', 'src_path', 'template_path',
                      'env_file', 'env_file_encoding', 'env_secrets_dir'}

    # Get all fields from the Pydantic model
    logger.info(f"Found {len(app_settings.__fields__)} fields in AppSettings")
    for field_name in app_settings.__fields__.keys():
        if field_name in exclude_fields:
            continue

        value = getattr(app_settings, field_name)

        # Skip None values
        if value is None:
            continue

        # Determine setting type
        setting_type = 'string'
        if isinstance(value, bool):
            setting_type = 'boolean'
        elif isinstance(value, int):
            setting_type = 'integer'
        elif isinstance(value, float):
            setting_type = 'float'
        elif isinstance(value, (list, dict)):
            setting_type = 'json'

        # Only create if doesn't exist (don't override existing DB values)
        if not GlobalSetting.objects.filter(key=field_name).exists():
            try:
                set_setting(
                    field_name,
                    value,
                    setting_type,
                    f'Setting from AppSettings: {field_name}'
                )
                synced += 1
                logger.debug(f"Synced {field_name} = {value}")
            except Exception as e:
                logger.warning(f"Failed to sync {field_name}: {e}")

    logger.info(f"✓ Synced {synced} settings from AppSettings to database")
    return synced


def load_db_settings_to_cache():
    """
    Load all settings from database into cache.
    Call this on Django startup via AppConfig.ready()
    """
    from apps.globalSettings.models import GlobalSetting

    settings_dict = {}
    count = 0

    for setting in GlobalSetting.objects.all():
        try:
            value = setting.get_value()
            settings_dict[setting.key] = value
            # Cache individual settings (never expire)
            cache.set(f'global_setting_{setting.key}', value, None)
            count += 1
        except Exception as e:
            logger.warning(f"Failed to load setting {setting.key}: {e}")

    # Cache all settings together
    cache.set('all_global_settings', settings_dict, None)

    logger.info(f"✓ Loaded {count} settings from database into cache")
    return settings_dict


def get_all_settings(use_cache=True):
    """
    Get all settings as a dictionary.

    Args:
        use_cache: Whether to use cache (default: True)

    Returns:
        Dictionary of all settings with keys and converted values
    """
    from apps.globalSettings.models import GlobalSetting

    cache_key = 'all_global_settings'

    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    settings_dict = {}
    for setting in GlobalSetting.objects.all():
        settings_dict[setting.key] = setting.get_value()

    if use_cache:
        cache.set(cache_key, settings_dict, None)

    return settings_dict