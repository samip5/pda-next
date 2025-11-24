import typing

from django.http import HttpRequest
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework_api_key.permissions import BaseHasAPIKey

from .helpers import get_user_from_request
from .models import UserAPIKey
from .accounts.models.account import AccountMembership
from .dns.models.zone import Zone


class HasUserAPIKey(BaseHasAPIKey):
    model = UserAPIKey

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        has_perm = super().has_permission(request, view)
        if has_perm:
            # Populate request.user object for convenience when API key is valid
            user = get_user_from_request(request)
            if user:
                request.user = user  # type: ignore
        return has_perm


# Hybrid permission class that can check for API keys or authentication
IsAuthenticatedOrHasUserAPIKey = IsAuthenticated | HasUserAPIKey


class IsAccountMember(BasePermission):
    message = "You must be a member of this account to access it."

    def _get_account_id(self, request: HttpRequest, view) -> typing.Optional[str]:
        return (
            getattr(view, 'kwargs', {}).get('user_id')
            or getattr(request, 'data', {}).get('account')
            or getattr(request, 'query_params', {}).get('account_id')
        )

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        user = get_user_from_request(request)
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        account_id = self._get_account_id(request, view)
        if not account_id:
            # No specific account targeted (e.g., listing) – allow authenticated users
            return True

        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True

        return AccountMembership.objects.filter(user=user, account_id=account_id).exists()


class IsAccountAdminOrOwner(BasePermission):
    message = "You must be an admin or owner of this account to perform this action."

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        user = get_user_from_request(request)
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        account_id = (
            getattr(view, 'kwargs', {}).get('user_id')
            or getattr(request, 'data', {}).get('account')
            or getattr(request, 'query_params', {}).get('account_id')
        )
        if not account_id:
            # Without an account context we don't allow modifying operations
            return False

        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True

        return AccountMembership.objects.filter(
            user=user,
            account_id=account_id,
            role__in=[AccountMembership.Role.ADMIN, AccountMembership.Role.OWNER],
        ).exists()


class IsZoneAccountMember(BasePermission):
    """Allows access to zone operations if user is a member of the zone's account.

    Zone name can come from view.kwargs['zone_name'], request.data['zone_name'], or query params.
    For zones not yet persisted (ephemeral responses from PowerDNS), we fall back to an
    'account' value in the request payload (e.g., when creating/updating).
    Superuser/staff bypass membership checks.
    """
    message = "You must belong to the account associated with this zone."

    def _normalize_zone_name(self, zone_name: str) -> str:
        return zone_name if zone_name.endswith('.') else zone_name + '.'

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        user = get_user_from_request(request)
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        zone_name = (
            getattr(view, 'kwargs', {}).get('zone_name')
            or getattr(request, 'data', {}).get('zone_name')
            or getattr(request, 'query_params', {}).get('zone_name')
        )

        if not zone_name:
            # No specific zone targeted – allow (listing zones may be filtered later)
            return True

        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True

        zone_name = self._normalize_zone_name(zone_name)
        zone = Zone.objects.filter(name=zone_name).first()

        if zone and zone.account_id:
            account_id = zone.account_id
        else:
            # Fallback: creation/update may carry account id directly
            account_id = getattr(request, 'data', {}).get('account') or getattr(request, 'query_params', {}).get('account')

        if not account_id:
            # Cannot determine account to check membership
            return False

        return AccountMembership.objects.filter(user=user, account_id=account_id).exists()


class IsZoneAccountAdminOrOwner(BasePermission):
    """Restricts zone modifications to account admins/owners (or superuser/staff)."""
    message = "You must be an admin or owner of the zone's account to modify this zone."

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        user = get_user_from_request(request)
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        zone_name = (
            getattr(view, 'kwargs', {}).get('zone_name')
            or getattr(request, 'data', {}).get('zone_name')
            or getattr(request, 'query_params', {}).get('zone_name')
        )
        if not zone_name:
            return False

        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True

        if not zone_name.endswith('.'):
            zone_name = zone_name + '.'

        zone = Zone.objects.filter(name=zone_name).first()
        if zone and zone.account_id:
            account_id = zone.account_id
        else:
            account_id = getattr(request, 'data', {}).get('account') or getattr(request, 'query_params', {}).get('account')

        if not account_id:
            return False

        return AccountMembership.objects.filter(
            user=user,
            account_id=account_id,
            role__in=[AccountMembership.Role.ADMIN, AccountMembership.Role.OWNER],
        ).exists()


# Composite convenience aliases (DRF supports bitwise composition)
CanViewAccount = IsAuthenticatedOrHasUserAPIKey & IsAccountMember
CanManageAccount = IsAuthenticatedOrHasUserAPIKey & IsAccountAdminOrOwner
CanViewZone = IsAuthenticatedOrHasUserAPIKey & IsZoneAccountMember
CanManageZone = IsAuthenticatedOrHasUserAPIKey & IsZoneAccountAdminOrOwner

__all__ = [
    'HasUserAPIKey',
    'IsAuthenticatedOrHasUserAPIKey',
    'IsAccountMember',
    'IsAccountAdminOrOwner',
    'IsZoneAccountMember',
    'IsZoneAccountAdminOrOwner',
    'CanViewAccount',
    'CanManageAccount',
    'CanViewZone',
    'CanManageZone',
]
