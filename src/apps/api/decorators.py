"""Reusable decorators to apply permission classes globally and per HTTP method.

Usage examples:

    from apps.api.decorators import use_permissions, method_permissions
    from apps.api.permissions import CanViewZone, CanManageZone

    @method_permissions({
        'GET': [CanViewZone],
        'POST': [CanManageZone],
        'DELETE': [CanManageZone],
    })
    def zone(self, request, zone_name=None):
        ...

Add MethodPermissionMixin to your ViewSet to make these effective.
"""
from functools import wraps
from typing import Iterable, Type, Dict

from rest_framework.exceptions import PermissionDenied
from django.http import HttpRequest

# Type alias for permission class type
PermissionClass = Type


def use_permissions(*permission_classes: PermissionClass):
    """Attach static permission classes to a view method for MethodPermissionMixin to pick up."""
    def decorator(func):
        func.permission_classes = list(permission_classes)
        return func
    return decorator


def method_permissions(mapping: Dict[str, Iterable[PermissionClass]]):
    """Attach per-HTTP method permission mapping to a view method.

    mapping keys are HTTP method names (e.g., 'GET', 'POST'). Values are iterables
    of permission class types.
    """
    normalized = {method.upper(): list(perms) for method, perms in mapping.items()}

    def decorator(func):
        func.method_permission_mapping = normalized
        return func
    return decorator


def require_permissions(*permission_classes: PermissionClass):
    """Immediate enforcement decorator (permission checked inside method).

    Not used by DRF's global permission evaluation phase; instead it executes
    validation when the method is invoked. Useful for secondary runtime checks.
    """
    def decorator(func):
        @wraps(func)
        def wrapped(self, request: HttpRequest, *args, **kwargs):
            for perm_cls in permission_classes:
                perm = perm_cls()
                if not perm.has_permission(request, self):
                    raise PermissionDenied(getattr(perm, 'message', 'Permission denied'))
            return func(self, request, *args, **kwargs)
        return wrapped
    return decorator


class MethodPermissionMixin:
    """Mixin to enable method-level permission resolution.

    Precedence:
    1. method.method_permission_mapping (per HTTP method mapping)
    2. method.permission_classes (static list for method)
    3. view.permission_classes (default DRF behavior)
    """
    def get_permissions(self):  # type: ignore[override]
        action_name = getattr(self, 'action', None)
        method_callable = getattr(self, action_name, None)
        req = getattr(self, 'request', None)  # type: ignore[attr-defined]
        if method_callable is not None and req is not None:
            # Per-method mapping first
            mapping = getattr(method_callable, 'method_permission_mapping', None)
            if mapping:
                classes = mapping.get(getattr(req, 'method', 'GET').upper())
                if classes:
                    return [cls() for cls in classes]
            # Static permission_classes attached to method
            static_classes = getattr(method_callable, 'permission_classes', None)
            if static_classes:
                return [cls() for cls in static_classes]
        # Fallback to view-level permission_classes
        return [permission() for permission in getattr(self, 'permission_classes', [])]

__all__ = [
    'use_permissions',
    'method_permissions',
    'require_permissions',
    'MethodPermissionMixin',
]
