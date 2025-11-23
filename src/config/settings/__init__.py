# Package initializer for config.settings — keeps this directory a package so
# modules like `config.settings.dev` or `config.settings.prod` are importable.

# Expose a small convenience to choose environment-specific settings via PDA_ENV
import os

_env = os.getenv('PDA_ENV', os.getenv('PDA_ENV_TYPE', 'production')).lower()

if _env in ('dev', 'development'):
    from .dev import *  # noqa: F401,F403
else:
    from .prod import *  # noqa: F401,F403
