# Minimal settings loader that delegates to environment-specific modules in config.settings
# Set PDA_ENV=development to load dev settings, PDA_ENV=production (default) to load prod.
# PDA_DEBUG (truthy) will force development settings.

import os

env = os.getenv('PDA_ENV', os.getenv('PDA_ENV_TYPE', 'production')).lower()
if os.getenv('PDA_DEBUG', 'False').lower() in ('1', 'true', 'yes'):
    env = 'development'

if env in ('dev', 'development'):
    from config.settings.dev import *  # noqa: F401,F403
else:
    from config.settings.prod import *  # noqa: F401,F403
