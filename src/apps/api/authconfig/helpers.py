from __future__ import annotations
import os
from typing import Any, Dict, Set

from config import settings as app_settings
from config import ROOT_PATH

try:
    from apps.api.dns.models.settings import Setting as DbSetting
except Exception:  # pragma: no cover - during collect/migrate
    DbSetting = None  # type: ignore

# Whitelisted setting names and their expected types
ALLOWED_GLOBAL_SETTINGS: dict[str, type] = {
    'maintenance': bool,
    'disable_local_auth': bool,
    'ldap_enabled': bool,
    'ldap_server_uri': str,
    'ldap_bind_dn': str,
    'ldap_bind_password': str,
    'ldap_user_search_base': str,
    'ldap_user_search_filter': str,
    'ldap_start_tls': bool,
    'ldap_user_attr_map': dict,
}

LDAP_SETTING_KEYS = [
    'ldap_enabled',
    'ldap_server_uri',
    'ldap_bind_dn',
    'ldap_bind_password',
    'ldap_user_search_base',
    'ldap_user_search_filter',
    'ldap_start_tls',
    'ldap_user_attr_map',
]


class SettingValidationError(ValueError):
    """Raised when a setting fails validation"""


def _validate(name: str, value: Any) -> None:
    expected = ALLOWED_GLOBAL_SETTINGS.get(name)
    if expected is None:
        raise SettingValidationError(f"Unknown setting '{name}'")

    if expected is bool and not isinstance(value, bool):
        raise SettingValidationError(f"Setting '{name}' must be a boolean")
    if expected is str and not (isinstance(value, str) or value is None):
        raise SettingValidationError(f"Setting '{name}' must be a string or None")
    if expected is dict and not (isinstance(value, dict) or value is None):
        raise SettingValidationError(f"Setting '{name}' must be a dict or None")


def get_setting(name: str) -> Any:
    """Return a single global setting (None if missing)."""
    if name not in ALLOWED_GLOBAL_SETTINGS:
        return None
    return getattr(app_settings, name, None)


def set_setting(name: str, value: Any) -> None:
    """Set a single global setting after validating type."""
    _validate(name, value)
    setattr(app_settings, name, value)


def bulk_set(settings_map: Dict[str, Any]) -> tuple[dict, dict]:
    """Bulk update settings. Returns (updated, errors)."""
    updated: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name, value in settings_map.items():
        try:
            _validate(name, value)
            setattr(app_settings, name, value)
            updated[name] = getattr(app_settings, name)
        except SettingValidationError as e:
            errors[name] = str(e)
    return updated, errors


def toggle_setting(name: str) -> Any:
    """Toggle a boolean setting and return the new value."""
    if ALLOWED_GLOBAL_SETTINGS.get(name) is not bool:
        raise SettingValidationError(f"Setting '{name}' is not boolean; cannot toggle.")
    current = bool(getattr(app_settings, name))
    setattr(app_settings, name, not current)
    return getattr(app_settings, name)


def get_ldap_config() -> dict[str, Any]:
    """Return current LDAP configuration as a dict."""
    return {k: getattr(app_settings, k, None) for k in LDAP_SETTING_KEYS}


def set_ldap_config(**kwargs) -> dict[str, Any]:
    """Update LDAP-related settings. Only keys in LDAP_SETTING_KEYS are applied."""
    for key, value in kwargs.items():
        if key in LDAP_SETTING_KEYS:
            _validate(key, value)
            setattr(app_settings, key, value)
    return get_ldap_config()


def disable_local_auth() -> None:
    set_setting('disable_local_auth', True)


def enable_local_auth() -> None:
    set_setting('disable_local_auth', False)


def is_local_auth_disabled() -> bool:
    return bool(getattr(app_settings, 'disable_local_auth', False))


# -------- Env preference helpers --------

def _discover_env_file_path() -> str:
    env_type = os.getenv('PDA_ENV_TYPE', 'production')
    # PDA_ENV_FILE can force a specific path
    forced = os.getenv('PDA_ENV_FILE')
    if forced:
        return forced
    env_file_name = f'.env.{env_type}'
    candidate = os.path.join(str(ROOT_PATH), env_file_name)
    if os.path.exists(candidate):
        return candidate
    candidate = os.path.join(str(ROOT_PATH), '.env')
    if os.path.exists(candidate):
        return candidate
    return '/etc/pda/.env'


def _parse_env_file_keys(path: str) -> Set[str]:
    keys: Set[str] = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                if '=' in s:
                    k = s.split('=', 1)[0].strip()
                    if k:
                        keys.add(k)
    except Exception:
        pass
    return keys


def _env_keys_set() -> Set[str]:
    keys = {k for k in os.environ.keys() if k.upper().startswith('PDA_')}
    file_path = _discover_env_file_path()
    keys |= _parse_env_file_keys(file_path)
    return {k.upper() for k in keys}


def _env_var_name_for(field_name: str) -> str:
    return f"PDA_{field_name}".upper()


def is_overridden_by_env(field_name: str) -> bool:
    return _env_var_name_for(field_name) in _env_keys_set()


def apply_db_settings_prefer_env() -> None:
    """Apply DB global settings with precedence rules:
    - Env (.env/process) has highest precedence and is never overridden
    - DB settings override YAML or defaults when env did not set the field
    """
    if DbSetting is None:
        return
    try:
        names = list(ALLOWED_GLOBAL_SETTINGS.keys())
        db_values: dict[str, Any] = {}
        for name in names:
            val = DbSetting.get(name)
            if val is not None:
                db_values[name] = val
        for name, value in db_values.items():
            if not is_overridden_by_env(name):
                try:
                    set_setting(name, value)
                except SettingValidationError:
                    pass
    except Exception:
        return

__all__ = [
    'ALLOWED_GLOBAL_SETTINGS',
    'LDAP_SETTING_KEYS',
    'SettingValidationError',
    'get_setting',
    'set_setting',
    'bulk_set',
    'toggle_setting',
    'get_ldap_config',
    'set_ldap_config',
    'disable_local_auth',
    'enable_local_auth',
    'is_local_auth_disabled',
    'is_overridden_by_env',
    'apply_db_settings_prefer_env',
]
