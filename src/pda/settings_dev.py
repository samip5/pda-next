"""
Django development settings for PDA project.

This file extends the base settings and overrides them with development-friendly values.
To use this configuration, set DJANGO_SETTINGS_MODULE=pda.settings_dev
"""

import os
from .settings import *

# Override DEBUG - always True in development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# Disable security features that are annoying in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
USE_HTTPS_IN_ABSOLUTE_URLS = False
SECURE_HSTS_SECONDS = 0

# Use a local SQLite database for easier development
# This will be created in the project root if not specified
# Override database configuration for development convenience
if not settings.db_url:
    db_path = os.path.join(settings.root_path, 'db.sqlite3')
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
    }

# Use console email backend to see emails in terminal
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Enable debug toolbar in development
if 'debug_toolbar' not in INSTALLED_APPS:
    INSTALLED_APPS.append('debug_toolbar')

# Ensure debug toolbar middleware is first
if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Internal IPs for debug toolbar (add your local IP if needed)
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Add more verbose logging in development
#LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['pda']['level'] = 'DEBUG'

# Add a console handler without debug filter for config logger
# (needed because config.py is imported before Django's DEBUG is set)
LOGGING['handlers']['console_config'] = {
    'class': 'logging.StreamHandler',
    'formatter': 'verbose',
    'level': 'DEBUG',
}

# Explicitly configure pda.config logger for development
LOGGING['loggers']['pdadns'] = {
    'handlers': ['console_config'],
    'level': 'DEBUG',
    'propagate': False,
}

# Disable email verification in development for easier testing
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Use a simple secret key for development (change in production!)
if settings.secret_key == 'INSECURE-CHANGE-ME-6up8zksTD6mi4N3z3zFk':
    SECRET_KEY = 'dev-secret-key-change-in-production-12345'

# Print SQL queries in development (useful for debugging)
#if DEBUG:
#    LOGGING['loggers']['django.db.backends'] = {
#        'handlers': ['console'],
#        'level': 'DEBUG',
#        'propagate': False,
#    }

