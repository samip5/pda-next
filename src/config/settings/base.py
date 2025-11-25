"""
Base Django settings for the project.
This file contains the bulk of the project's settings and is intended to be imported
by environment-specific settings modules (dev, prod) which can override values.
"""
import sys
import os
import logging
from pathlib import Path
from django.utils.translation import gettext_lazy

config_parent = Path(__file__).resolve().parents[1]
logger = logging.getLogger("pda")
logger.debug("Config parent directory: {}".format(config_parent))
sys.path.append(str(config_parent))
if str(config_parent) not in sys.path:
    sys.path.insert(0, str(config_parent))

from config import load_settings, load_config, env_conf_path

app_settings = load_settings(env_conf_path)
app_settings = load_config(app_settings)

SECRET_KEY = app_settings.secret_key
DEBUG = app_settings.debug
ALLOWED_HOSTS = app_settings.allowed_hosts
SECURE_SSL_REDIRECT = app_settings.secure_ssl_redirect
SESSION_COOKIE_SECURE = app_settings.session_cookie_secure
CSRF_COOKIE_SECURE = app_settings.csrf_cookie_secure
USE_HTTPS_IN_ABSOLUTE_URLS = app_settings.use_https_in_absolute_urls

if isinstance(app_settings.secure_hsts_seconds, int) and app_settings.secure_hsts_seconds > 0:
    SECURE_HSTS_SECONDS = app_settings.secure_hsts_seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = app_settings.secure_hsts_include_subdomains
    SECURE_HSTS_PRELOAD = app_settings.secure_hsts_preload

if isinstance(app_settings.secure_proxy_ssl_header_name, str) and len(app_settings.secure_proxy_ssl_header_name.strip()) \
        and isinstance(app_settings.secure_proxy_ssl_header_value, str) \
        and len(app_settings.secure_proxy_ssl_header_value.strip()):
    SECURE_PROXY_SSL_HEADER = (app_settings.secure_proxy_ssl_header_name, app_settings.secure_proxy_ssl_header_value)

ROOT_URLCONF = "pda.urls"
WSGI_APPLICATION = "pda.wsgi.application"
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
SITE_ID = 1

PROJECT_METADATA = {
    'NAME': gettext_lazy(app_settings.site_title),
    'URL': app_settings.site_url,
    'DESCRIPTION': gettext_lazy(app_settings.site_description),
    'IMAGE': app_settings.site_logo,
    'KEYWORDS': 'pdns, powerdns, pda, admin, manage, console, dns, domain, nameserver, recursor, cache, authoritative, '
                + 'dnssec, app, ui',
    'CONTACT_EMAIL': app_settings.site_email,
}

powerdns_api_url = app_settings.powerdns_api_url
powerdns_api_key = app_settings.powerdns_api_key
powerdns_api_timeout = 30

# Internationalization / Localization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = app_settings.language_code
LANGUAGE_COOKIE_NAME = app_settings.language_cookie_name
LANGUAGES = [
    ('en', gettext_lazy('English')),
    ('fi', gettext_lazy('Finnish')),
]
LOCALE_PATHS = (os.path.join(app_settings.src_path, 'locale'),)
TIME_ZONE = app_settings.time_zone
USE_I18N = app_settings.use_i18n
USE_L10N = app_settings.use_l10n
USE_TZ = app_settings.use_tz

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(app_settings.src_path, 'static_root')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(app_settings.src_path, 'static')]

# uncomment to use manifest storage to bust cache when file change
# note: this may break some image references in sass files which is why it is not enabled by default
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

MEDIA_ROOT = os.path.join(app_settings.root_path, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

# future versions of Django will use BigAutoField as the default, but it can result in unwanted library
# migration files being generated, so we stick with AutoField for now.
# change this to BigAutoField if you're sure you want to use it and aren't worried about migrations.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.forms",
]

# Put your third-party apps here
THIRD_PARTY_APPS = [
    "allauth",  # allauth account/registration management
    "allauth.account",
    "allauth.socialaccount",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "allauth_2fa",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_api_key",
    "celery_progress",
    "waffle",
    "debug_toolbar"
]

# Put your project-specific apps here
PROJECT_APPS = [
    "apps.users.apps.UserConfig",
    "apps.api.apps.APIConfig",
    "apps.web",
    "apps.api.dns.apps.DNSConfig",
    "apps.api.accounts.apps.AccountsConfig",
    "apps.api.activity.apps.ActivityConfig",
    "apps.api.templates.apps.ActivityConfig",
    "apps.globalSettings.apps.GlobalSettingsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "pda.middleware.CoreMiddleware",  # Core middleware for request logging and Sentry tracing
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "apps.web.locale_middleware.UserLocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [app_settings.template_path, ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.web.context_processors.project_meta",
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [app_settings.template_path, ],
        'APP_DIRS': False,
        'OPTIONS': {
            'environment': 'pda.jinja2.JinjaEnvironment',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "apps.web.context_processors.project_meta",
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {}

if isinstance(app_settings.db_url, str) and len(app_settings.db_url.strip()):
    import environ

    env = environ.Env()
    DATABASES['default'] = env.db_url_config(url=app_settings.db_url)

    if 'NAME' in DATABASES['default'] and isinstance(DATABASES['default']['NAME'], str) and len(
            DATABASES['default']['NAME'].strip()):
        DATABASES['default']['NAME'] = os.path.join(app_settings.root_path, DATABASES['default']['NAME'])
else:
    db: dict = {}
    db_engine: str = app_settings.db_engine.lower()

    if db_engine == 'sqlite':
        db = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': app_settings.db_path,
        }

    elif db_engine in ['mysql', 'postgresql']:
        db = {
            'HOST': app_settings.db_host,
            'PORT': app_settings.db_port,
            'USER': app_settings.db_user,
            'PASSWORD': app_settings.db_password,
            'NAME': app_settings.db_name,
        }

        if db_engine == 'mysql':
            db['ENGINE'] = 'django.db.backends.mysql'
            db['OPTIONS'] = {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
            }

        elif db_engine == 'postgresql':
            db['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

    else:
        raise ValueError(f'Invalid database engine specified: {db_engine}')

    if bool(db):
        DATABASES['default'] = db
    else:
        raise ValueError('Invalid database configuration detected')

# Auth Setup

# Django recommends overriding the user model even if you don't think you need to because it makes
# future changes much easier.
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Allauth setup

ACCOUNT_ADAPTER = 'apps.users.adapter.AccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = app_settings.account_authentication_method
ACCOUNT_EMAIL_REQUIRED = app_settings.account_email_required
ACCOUNT_EMAIL_SUBJECT_PREFIX = app_settings.email_subject_prefix
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = app_settings.account_username_required
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False

# User signup configuration: change to "mandatory" to require users to confirm email before signing in.
# or "optional" to send confirmation emails but not require them
ACCOUNT_EMAIL_VERIFICATION = app_settings.account_email_verification

ALLAUTH_2FA_ALWAYS_REVEAL_BACKUP_TOKENS = False

# LDAP Configuration
#AUTH_LDAP_SERVER_URI = os.environ.get('AUTH_LDAP_SERVER_URI', 'ldap://ldap.example.com')
#AUTH_LDAP_BIND_DN = os.environ.get('AUTH_LDAP_BIND_DN', '')
#AUTH_LDAP_BIND_PASSWORD = os.environ.get('AUTH_LDAP_BIND_PASSWORD', '')
#AUTH_LDAP_USER_SEARCH = LDAPSearch(
#    'ou=users,dc=example,dc=com',
#    ldap.SCOPE_SUBTREE,
#    '(uid=%(user)s)'
#)
#AUTH_LDAP_USER_ATTR_MAP = {
#    "first_name": "givenName",
#    "last_name": "sn",
#    "email": "mail"
#}

AUTHENTICATION_BACKENDS = (
#    'django_auth_ldap.backend.LDAPBackend',
    # Needed to log in by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Email setup

EMAIL_BACKEND = None
if isinstance(app_settings.email_backend, str) and len(app_settings.email_backend.strip()):
    ADMINS = [(app_settings.admin_name, app_settings.admin_email)]
    DEFAULT_FROM_EMAIL = app_settings.site_from_email
    SERVER_EMAIL = app_settings.admin_from_email
    EMAIL_BACKEND = app_settings.email_backend
    EMAIL_HOST = app_settings.email_host
    EMAIL_HOST_PASSWORD = app_settings.email_host_password
    EMAIL_HOST_USER = app_settings.email_host_user
    EMAIL_PORT = app_settings.email_port
    EMAIL_SSL_CERTFILE = app_settings.email_ssl_certfile
    EMAIL_SSL_KEYFILE = app_settings.email_ssl_keyfile
    EMAIL_SUBJECT_PREFIX = app_settings.email_subject_prefix
    EMAIL_TIMEOUT = app_settings.email_timeout
    EMAIL_USE_SSL = app_settings.email_use_ssl
    EMAIL_USE_TLS = app_settings.email_use_tls

# DRF config
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('apps.api.permissions.IsAuthenticatedOrHasUserAPIKey',),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'apps.api.renderers.APIRequestLogRenderer',
        'rest_framework.renderers.JSONRenderer',
    ],
    # API Versioning configuration
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'ALLOWED_VERSIONS': ['v1'],  # Add new versions here as they're created
    'DEFAULT_VERSION': 'v1',  # Default version if none specified
    'VERSION_PARAM': 'version',  # URL parameter name for version
}

SPECTACULAR_SETTINGS = {
    'TITLE': app_settings.site_title,
    'DESCRIPTION': app_settings.site_description,
    'VERSION': app_settings.version,
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'displayOperationId': True,
    },
    'PREPROCESSING_HOOKS': [
        'apps.api.schema.filter_schema_apis',
    ],
    'APPEND_COMPONENTS': {
        'securitySchemes': {'ApiKeyAuth': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}}
    },
    'SECURITY': [
        {
            'ApiKeyAuth': [],
        }
    ],
    # Versioning support - drf-spectacular will automatically detect versions from URLPathVersioning
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',  # Match versioned API paths
}

REDIS_URL: str | None = None
if isinstance(app_settings.redis_url, str) and len(app_settings.redis_url.strip()):
    REDIS_URL = app_settings.redis_url
elif isinstance(app_settings.redis_host, str) and len(app_settings.redis_host.strip()):
    REDIS_HOST = app_settings.redis_host
    REDIS_PORT = app_settings.redis_port
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

if isinstance(REDIS_URL, str):
    # Disable REDIS SSL cert verification if using rediss:// protocol
    if REDIS_URL.startswith('rediss'):
        REDIS_URL += '?ssl_cert_reqs=none'

    # Celery setup (using redis)
    CELERY_BROKER_URL = CELERY_RESULT_BACKEND = REDIS_URL

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {levelname} {message}',
            'style': '{',
        },
        'verbose': {
            'format': '[{asctime}] {levelname} "{name}" {message}',
            'style': '{',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'django.server': {
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': app_settings.log_level_django,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': app_settings.log_level_django,
            'propagate': False,
        },
        'pda': {
            'handlers': ['console'],
            'level': app_settings.log_level_app,
        },
    },
}


# Setup Sentry Exception Tracking with best practices
if isinstance(app_settings.sentry_dsn, str) and len(app_settings.sentry_dsn.strip()):
    from pda.utils.sentry import configure_sentry
    
    # Determine environment from DEBUG setting
    environment = 'development' if DEBUG else 'production'
    
    # Configure Sentry with best practices
    configure_sentry(
        dsn=app_settings.sentry_dsn,
        environment=environment,
        release=getattr(app_settings, 'version', None),
        traces_sample_rate=0.1,  # Sample 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # Sample 10% of transactions for profiling
        send_default_pii=False,  # Don't send PII by default
    )

