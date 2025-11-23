from .base import *

# Ensure DEBUG is disabled in production unless explicitly enabled in env
DEBUG = bool(os.getenv('PDA_DEBUG', 'False') in ['True', 'true', '1'])

# Tighten allowed hosts if provided
ALLOWED_HOSTS = os.getenv('PDA_ALLOWED_HOSTS', ','.join(ALLOWED_HOSTS)).split(',') if os.getenv('PDA_ALLOWED_HOSTS') else ALLOWED_HOSTS

# Ensure secure cookies and redirects
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# HSTS defaults (can be overridden via PDA_SECURE_HSTS_SECONDS)
SECURE_HSTS_SECONDS = int(os.getenv('PDA_SECURE_HSTS_SECONDS', globals().get('SECURE_HSTS_SECONDS', 2592000)))

# Logging level
LOGGING['loggers']['django']['level'] = os.getenv('PDA_LOG_LEVEL_DJANGO', settings.log_level_django)
LOGGING['loggers']['pda']['level'] = os.getenv('PDA_LOG_LEVEL_APP', settings.log_level_app)

