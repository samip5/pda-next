from pathlib import Path
import os
import yaml
import logging
from pydantic_settings import BaseSettings
from typing import Any

from typing_extensions import ClassVar

# Compute root paths correctly. This file lives at src/config/__init__.py so two parents up is the repo root.
ROOT_PATH: Path = Path(__file__).resolve().parents[2]
""" The root path of the application which is typically the project repository root path. """

SRC_PATH: Path = ROOT_PATH / 'src'
""" The source path of the application which is typically the src directory within the ROOT_PATH. """

TEMPLATE_PATH: Path = SRC_PATH / 'templates'
""" The template path of the application which is typically the templates directory within the SRC_PATH. """

logger = logging.getLogger("pda.config")
# Configure basic logging for config module (before Django's logging is initialized)
# Django will reconfigure this later when it initializes (disable_existing_loggers=False)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s "%(name)s" %(message)s',
        datefmt='%d/%b/%Y %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class AppSettings(BaseSettings):
    """ The application settings object that loads setting values from the application environment. """

    version: str = '0.1.0'
    """ The application version number """

    account_authentication_method: str = 'username_email'  # email, username, username_email
    account_email_required: bool = False
    account_email_verification: str = 'none'  # none, optional, required
    account_username_required: bool = False
    admin_email: str = 'admin@yourdomain.com'
    admin_from_email: str = 'noreply@yourdomain.com'
    admin_name: str = 'Admin'
    allowed_hosts: list[str] = ['*']
    config_path: str = '/etc/pda/config.yml'
    csrf_cookie_secure: bool = True
    debug: bool = False
    db_engine: str = 'sqlite'  # mysql, postgresql, sqlite
    db_host: str | None = None
    db_name: str | None = None
    db_password: str | None = None
    db_path: str | None = '/var/lib/pda/pda.db'
    db_port: int = 0
    db_url: str | None = None
    db_user: str | None = None
    email_backend: str | None = None
    email_host: str = 'localhost'
    email_host_user: str | None = None
    email_host_password: str | None = None
    email_port: int = 587
    email_ssl_certfile: str | None = None
    email_ssl_keyfile: str | None = None
    email_subject_prefix: str | None = '[PDA] '
    email_timeout: int = 0
    email_use_ssl: bool = False
    email_use_tls: bool = True
    env_file: str = '/etc/pda/.env'
    env_file_encoding: str = 'UTF-8'
    env_secrets_dir: str = '/run/secrets'
    env_type: str | None = 'production'  # development, production
    google_analytics_id: str | None = None
    language_code: str = 'en-us'
    language_cookie_name: str = 'pdns_admin_language'
    log_level_app: str = 'INFO'
    log_level_django: str = 'INFO'
    log_path: str = '/var/log/pda/pda.log'
    log_retention: int = 30
    log_rotation: str = 'daily'  # daily, weekly, monthly
    log_size: int = 10000000
    log_to_file: bool = False
    log_to_sentry: bool = False
    log_to_stdout: bool = True
    log_to_syslog: bool = False
    maintenance: bool = False
    redis_host: str = ''
    redis_password: str | None = None
    redis_port: int = 6379
    redis_url: str = ''
    root_path: str = str(ROOT_PATH)
    secret_key: str = 'INSECURE-CHANGE-ME-6up8zksTD6mi4N3z3zFk'
    secure_hsts_include_subdomains: bool = True
    secure_hsts_preload: bool = True
    secure_hsts_seconds: int | str | None = 2592000
    secure_proxy_ssl_header_name: str = 'HTTP_X_FORWARDED_PROTO'
    secure_proxy_ssl_header_value: str = 'https'
    secure_ssl_redirect: bool = True
    sentry_dsn: str = ''

    server_address: str = '0.0.0.0'
    server_port: int = 8080
    server_type: str | None = 'gunicorn'  # gunicorn, uvicorn, uwsgi, django

    session_cookie_secure: bool = True
    site_description: str = 'A PowerDNS web interface with advanced features.'
    site_email: str = 'pda@yourdomain.com'
    site_from_email: str = 'pda@yourdomain.com'
    site_logo: str | None = None
    site_title: str = 'PowerDNS Admin'
    site_name: str = 'PowerDNS Admin'
    site_url: str = 'https://pda.yourdomain.com'
    src_path: str = str(SRC_PATH)
    syslog_host: str | None = None
    syslog_port: int = 514
    template_path: str = str(TEMPLATE_PATH)
    time_zone: str = 'UTC'
    use_https_in_absolute_urls: bool = True
    use_i18n: bool = True
    use_l10n: bool = True
    use_tz: bool = True
    venv_enabled: bool = False
    venv_path: str | None = 'venv'
    powerdns_api_url: str = ''
    powerdns_api_key: str = ''
    powerdns_api_timeout: int = 30
    disable_landing_page: bool = False
    auth_ldap_start_tls: bool = False
    auth_ldap_server_uri: str = ''
    auth_ldap_bind_dn: str = ''
    auth_ldap_bind_password: str = ''
    auth_ldap_create_users: bool = True
    auth_ldap_user_search_base: str = ''
    auth_ldap_user_search_filter: str = ''
    ldap_enable: bool = False
    record_types: dict[str, bool] = {
        'A': True,
        'AAAA': True,
        'AFSDB': False,
        'ALIAS': True,
        'CAA': True,
        'CERT': False,
        'CDNSKEY': False,
        'CDS': False,
        'CNAME': True,
        'DNSKEY': False,
        'DNAME': False,
        'DS': False,
        'HINFO': False,
        'KEY': False,
        'LOC': True,
        'LUA': False,
        'MX': True,
        'NAPTR': False,
        'NS': True,
        'NSEC': False,
        'NSEC3': False,
        'NSEC3PARAM': False,
        'OPENPGPKEY': False,
        'PTR': True,
        'RP': False,
        'RRSIG': False,
        'SOA': False,
        'SPF': True,
        'SSHFP': False,
        'SRV': True,
        'TKEY': False,
        'TSIG': False,
        'TLSA': False,
        'SMIMEA': False,
        'TXT': True,
        'URI': False
    }
    reverse_record_types: dict[str, bool] = {
        'A': False,
        'AAAA': False,
        'AFSDB': False,
        'ALIAS': False,
        'CAA': False,
        'CERT': False,
        'CDNSKEY': False,
        'CDS': False,
        'CNAME': False,
        'DNSKEY': False,
        'DNAME': False,
        'DS': False,
        'HINFO': False,
        'KEY': False,
        'LOC': True,
        'LUA': False,
        'MX': False,
        'NAPTR': False,
        'NS': True,
        'NSEC': False,
        'NSEC3': False,
        'NSEC3PARAM': False,
        'OPENPGPKEY': False,
        'PTR': True,
        'RP': False,
        'RRSIG': False,
        'SOA': False,
        'SPF': False,
        'SSHFP': False,
        'SRV': False,
        'TKEY': False,
        'TSIG': False,
        'TLSA': False,
        'SMIMEA': False,
        'TXT': True,
        'URI': False
    }


    """ The following settings are automatically loaded at application startup. """

    config: dict | None = None
    """ Additional configuration settings loaded automatically from the given YAML configuration file (if any) """

    class Config:
        env_prefix = 'pda_'


def load_settings(env_file_path: str = '/etc/pda/.env', env_file_encoding: str = 'UTF-8',
                  secrets_path: str | None = None) -> AppSettings:
    """ Loads an AppSettings instance based on the given environment file and secrets directory. """

    params: dict = {
        '_env_file': env_file_path,
        '_env_file_encoding': env_file_encoding,
    }

#    os.putenv('PDA_ENV_FILE', env_file_path)
#    os.putenv('PDA_ENV_FILE_ENCODING', env_file_encoding)

#    logger.debug(f"Loading config using env file {env_file_path}")


    # Load base app configuration settings from the given environment file and the local environment
    app_settings = AppSettings(**params)

    #logger.debug(app_settings)

    # Prepend the root path to the database path if it is not an absolute path
    if isinstance(app_settings.db_path, str) and len(
            app_settings.db_path.strip()) and not app_settings.db_path.startswith('/'):
        app_settings.db_path = str(os.path.join(app_settings.root_path, app_settings.db_path))

    return app_settings


def load_config(app_settings: AppSettings) -> AppSettings:
    """ Loads the app's configuration from the given configuration file. """
    from yaml import YAMLError

    config_path: str | None = app_settings.config_path

    if not isinstance(config_path, str):
        return app_settings

    if len(config_path.strip()) == 0:
        return app_settings

    if not config_path.startswith('/'):
        config_path = os.path.join(app_settings.root_path, config_path)

    try:
        with open(config_path, 'r') as f:
            app_settings.config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()
    except FileNotFoundError:
        # print(f'The given path for the configuration file does not exist: {config_path}')
        pass
    except IsADirectoryError:
        # print(f'The given path for the configuration file is not a file: {config_path}')
        pass
    except PermissionError:
        # print(f'Permission denied when trying to read the configuration file: {config_path}')
        pass
    except UnicodeDecodeError:
        # print(f'Failed to decode the configuration file: {config_path}')
        pass
    except YAMLError as e:
        # print(f'Failed to parse the configuration file "{config_path}": {e}')
        pass

    return app_settings


def save_config(app_settings: AppSettings, config: dict[str, Any]) -> bool:
    """ Saves the app's configuration to the defined configuration file setting path. """

    config_path: str = app_settings.config_path

    if not config_path.startswith('/'):
        config_path = os.path.join(app_settings.root_path, config_path)

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
        f.close()

    return True


# Define the default environment file path to load settings from
env_type: str = os.getenv('PDA_ENV_TYPE', 'production')
env_conf_path: str | None = os.getenv('PDA_ENV_FILE')

if env_conf_path is None:
    # We check for environment specific env files first, e.g. .env.development
    env_file_name = f'.env.{env_type}'
    if os.path.exists(os.path.join(ROOT_PATH, env_file_name)):
        env_conf_path = os.path.join(ROOT_PATH, env_file_name)
    # If that doesn't exist, we check for a regular .env file
    elif os.path.exists(os.path.join(ROOT_PATH, '.env')):
        env_conf_path = os.path.join(ROOT_PATH, '.env')
    # Finally, we fall back to the old default
    else:
        env_conf_path = '/etc/pda/.env'

# Load various Django settings from an environment file and the local environment
app_settings: AppSettings = load_settings(env_conf_path)


def load_db_settings_to_config(app_settings: AppSettings) -> AppSettings:
    """
    Load settings from database and merge them into the AppSettings object.
    This is called during Django startup via AppConfig.ready()
    """
    try:
        # Import here to avoid circular imports
        from django.db import connection
        from django.core.cache import cache

        # Check if database tables exist (avoid issues during migrations)
        table_names = connection.introspection.table_names()
        logger.debug(f"Database tables: {table_names}")

        # Adjust table name based on your app name
        if 'global_settings' in table_names:
            from apps.globalSettings.models import GlobalSetting

            logger.info("Loading settings from database...")

            # Load all settings from DB
            db_settings = {}
            for setting in GlobalSetting.objects.all():
                db_settings[setting.key] = setting.get_value()
                # Cache individual settings
                cache.set(f'global_setting_{setting.key}', setting.get_value(), None)

            # Cache all settings
            cache.set('all_global_settings', db_settings, None)

            # Update app_settings with database values (DB overrides env vars)
            for key, value in db_settings.items():
                # Convert db setting keys to match AppSettings field names
                # e.g., 'site_title' in DB maps to app_settings.site_title
                if hasattr(app_settings, key):
                    setattr(app_settings, key, value)
                    logger.debug(f"Loaded setting from DB: {key} = {value}")

            logger.info(f"✓ Loaded {len(db_settings)} settings from database")

    except Exception as e:
        logger.warning(f"Could not load settings from database: {e}")

    return app_settings
