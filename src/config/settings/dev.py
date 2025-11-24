from .base import *
from pathlib import Path
from config import settings as app_settings

# Use the pydantic AppSettings instance (app_settings) for canonical paths and values.
BASE_DIR = Path(app_settings.root_path)

# Enable debug by default in dev
DEBUG = True

# Development database: sqlite file inside the project root
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db_dev.sqlite3'),
    }
}

# Allow localhost during development (defensive merge with project ALLOWED_HOSTS)
_base_allowed = list(ALLOWED_HOSTS) if isinstance(ALLOWED_HOSTS, (list, tuple)) else []
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '::1'] + _base_allowed

# Use simpler logging in dev — guard keys in case base logging is minimal
if isinstance(LOGGING, dict):
    handlers = LOGGING.setdefault('handlers', {})
    # ensure console handler exists
    console = handlers.get('console')
    if console and 'filters' in console:
        console['filters'] = []

    loggers = LOGGING.setdefault('loggers', {})
    if 'django' in loggers:
        loggers['django']['level'] = 'INFO'
    if 'pda' in loggers:
        loggers['pda']['level'] = 'DEBUG'

# Disable some production hardening for dev convenience
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
powerdns_api_url="http://172.8.0.20:8081/api/v1"
powerdns_api_key="secret"
powerdns_api_timeout=30000