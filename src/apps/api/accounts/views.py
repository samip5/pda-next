from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.decorators import MethodPermissionMixin, method_permissions
from apps.api.permissions import CanViewAccount, CanManageAccount, CanViewZone, CanManageZone

from .helpers import updateAccount
from .models.account import Account
from .serializers import AccountSerializer
from ..dns.models import Zone
from ..dns.serializers import ZoneSerializer
from ..dns.services import PowerDNSService


class AccountViewSet(MethodPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for fetching Accounts.

    Provides endpoints to list and retrieve Accounts from the database.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [CanViewAccount]

    def get_queryset(self):
        """
        Optionally restricts the returned records by filtering against
        query parameters in the URL.
        """
        queryset = Account.objects.all()

        # Filter by record name
        name = getattr(self.request, 'query_params', {}).get('name', None)  # type: ignore[attr-defined]
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')


    @action(detail=False, methods=['get', 'post'], url_path='manage')
    @method_permissions({'GET': [CanViewAccount], 'POST': [CanManageAccount]})
    def accounts(self, request):
        if request.method == 'GET':
            serializer = AccountSerializer(Account.objects.all(), many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            account_name = request.data.get('name', '')
            account = Account.objects.create(
                name=account_name,
            )
            serializer = AccountSerializer(account)
            return Response(serializer.data)

    @action(detail=False, methods=['get', 'post', 'delete'], url_path='manage/(?P<user_id>[^/]+)')
    @method_permissions({'GET': [CanViewAccount], 'POST': [CanManageAccount], 'DELETE': [CanManageAccount]})
    def account(self, request, user_id=None):
        if request.method == 'GET':
            account = Account.objects.filter(id=user_id).first()
            serializer = AccountSerializer(account, many=False)
            return Response(serializer.data)

        elif request.method == 'POST':
            account = updateAccount(user_id, request.data.get('name'), request.data.get('description'), request.data.get('contact'), request.data.get('mail'))

            serializer = AccountSerializer(account)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            account = Account.objects.filter(id=user_id).first()
            account.delete()
            return Response("Account deleted")


    @action(detail=False, methods=['get', 'post', 'delete'], url_path='manage/(?P<user_id>[^/]+)/zones')
    @method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone], 'DELETE': [CanManageZone]})
    def account_zones(self, request, user_id=None):
        account = Account.objects.filter(id=user_id).first()

        service = PowerDNSService()
        powerdns_zones = service.get_zones("localhost")

        # Convert PowerDNS record format to Record model instances (not saved)
        zone_instances = []
        for zone in powerdns_zones:
            zone_a = Zone(
                name=zone.get('name', ''),
                kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
                nameservers=zone.get('nameservers', []),
                server_id=zone.get('server_id', 'localhost'),
                powerdns_id=zone.get('id'),
                account=zone.get('account', ''),
                dnssec=zone.get('dnssec', '')
            )
            zone_instances.append(zone_a)

        account_zones = [zone for zone in zone_instances if zone.account == str(account.id)]

        serializer = ZoneSerializer(account_zones, many=True)
        return Response(serializer.data)
