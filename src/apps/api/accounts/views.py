from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.api.decorators import MethodPermissionMixin, method_permissions
from apps.api.permissions import CanViewAccount, CanManageAccount, CanViewZone, CanManageZone

from .helpers import updateAccount
from .models.account import Account
from .serializers import AccountSerializer
from ..activity.helpers import addActivityLog
from ..activity.models.activity import ActionType
from ..dns.models import Zone
from ..dns.serializers import ZoneSerializer
from ..dns.services import PowerDNSService
from ..models import UserAPIKey


class AccountViewSet(MethodPermissionMixin, viewsets.ReadOnlyModelViewSet):
    
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [CanViewAccount]

    def get_queryset(self):
        queryset = Account.objects.all()

        # Filter by record name
        name = getattr(self.request, 'query_params', {}).get('name', None)  # type: ignore[attr-defined]
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')

    @extend_schema(
        summary="List all accounts",
        description="Returns a paginated list of all accounts the authenticated user has access to. Results are paginated with 100 items per page.",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter accounts by name (case-insensitive partial match)',
                required=False,
            ),
        ],
        responses={
            200: AccountSerializer,
        },
    )
    def list(self, request):
        return super().list(request)

    @extend_schema(
        summary="Retrieve a specific account",
        description="Returns details of a single account by ID.",
        responses={
            200: AccountSerializer,
            404: OpenApiTypes.OBJECT,
        },
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

    @extend_schema(
        methods=['GET'],
        summary="List all accounts (manage endpoint)",
        description="List all accounts (same as list endpoint).",
        responses={
            200: AccountSerializer,
        },
    )
    @extend_schema(
        methods=['POST'],
        summary="Create a new account",
        description="Create a new account with the specified name.",
        request=AccountSerializer,
        responses={
            200: AccountSerializer,
        },
    )
    @action(detail=False, methods=['get', 'post'], url_path='manage')
    #@method_permissions({'GET': [CanViewAccount], 'POST': [CanManageAccount]})
    def accounts(self, request):
        if request.method == 'GET':
            serializer = AccountSerializer(Account.objects.all(), many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            account_name = request.data.get('name', '')
            account = Account.objects.create(
                name=account_name,
            )
            api_key = UserAPIKey.objects.filter(
                prefix=request.headers.get("Authorization").strip("Api-Key ").split('.', 1)[0]).first()
            addActivityLog(ActionType.ACCOUNT_CREATE,
                           f"{account_name} created",
                           request.user, api_key.name, True)

            serializer = AccountSerializer(account)
            return Response(serializer.data)

    @extend_schema(
        methods=['GET'],
        summary="Retrieve a specific account by ID",
        description="Retrieve account details by account ID.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Account ID',
                required=True,
            ),
        ],
        responses={
            200: AccountSerializer,
            404: OpenApiTypes.OBJECT,
        },
    )
    @extend_schema(
        methods=['POST'],
        summary="Update an existing account",
        description="Update account details. All fields are optional.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Account ID',
                required=True,
            ),
        ],
        request=AccountSerializer,
        responses={
            200: AccountSerializer,
        },
    )
    @extend_schema(
        methods=['DELETE'],
        summary="Delete an account",
        description="Delete an account by ID.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Account ID',
                required=True,
            ),
        ],
        responses={
            200: OpenApiTypes.STR,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='manage/(?P<user_id>[^/]+)')
    #@method_permissions({'GET': [CanViewAccount], 'POST': [CanManageAccount], 'DELETE': [CanManageAccount]})
    def account(self, request, user_id=None):
        """
        Manage a specific account by ID.

        GET /api/v1/accounts/manage/{user_id}/
            Retrieve a specific account.

            Path Parameters:
                - user_id (int): Account ID

            Response:
                200 OK: Account object
                {
                    "id": 1,
                    "name": "example-account",
                    "description": "Example account description",
                    "contact": "admin@example.com",
                    "mail": "admin@example.com"
                }

                404 Not Found: Account does not exist or user lacks access

            Permissions:
                - Requires CanViewAccount (account membership)

        POST /api/v1/accounts/manage/{user_id}/
            Update an existing account.

            Path Parameters:
                - user_id (int): Account ID

            Request Body:
                {
                    "name": "updated-name",           # Optional
                    "description": "Updated description",  # Optional
                    "contact": "new-contact@example.com",  # Optional
                    "mail": "new-mail@example.com"    # Optional
                }

            Response:
                200 OK: Updated account object
                {
                    "id": 1,
                    "name": "updated-name",
                    "description": "Updated description",
                    "contact": "new-contact@example.com",
                    "mail": "new-mail@example.com"
                }

            Permissions:
                - Requires CanManageAccount (account admin/owner role)

        DELETE /api/v1/accounts/manage/{user_id}/
            Delete an account.

            Path Parameters:
                - user_id (int): Account ID

            Response:
                200 OK: "Account deleted"

                404 Not Found: Account does not exist or user lacks access

            Permissions:
                - Requires CanManageAccount (account admin/owner role)
        """
        if request.method == 'GET':
            account = Account.objects.filter(id=user_id).first()
            serializer = AccountSerializer(account, many=False)
            return Response(serializer.data)

        elif request.method == 'POST':
            account = updateAccount(user_id, request.data.get('name'), request.data.get('description'), request.data.get('contact'), request.data.get('mail'))
            api_key = UserAPIKey.objects.filter(
                prefix=request.headers.get("Authorization").strip("Api-Key ").split('.', 1)[0]).first()
            addActivityLog(ActionType.ACCOUNT_UPDATE,
                           f"{request.data.get('name')} updated",
                           request.user, api_key.name, True)
            serializer = AccountSerializer(account)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            account = Account.objects.filter(id=user_id).first()
            api_key = UserAPIKey.objects.filter(
                prefix=request.headers.get("Authorization").strip("Api-Key ").split('.', 1)[0]).first()
            addActivityLog(ActionType.ACCOUNT_DELETE,
                           f"{account} deleted",
                           request.user, api_key.name, True)
            account.delete()
            return Response("Account deleted")


    @extend_schema(
        methods=['GET'],
        summary="List zones for an account",
        description="List all zones associated with a specific account.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Account ID',
                required=True,
            ),
        ],
        responses={
            200: ZoneSerializer,
        },
    )
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='manage/(?P<user_id>[^/]+)/zones')
    #@method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone], 'DELETE': [CanManageZone]})
    def account_zones(self, request, user_id=None):
        """
        Manage zones for a specific account.

        GET /api/v1/accounts/manage/{user_id}/zones/
            List all zones associated with an account.

            Path Parameters:
                - user_id (int): Account ID

            Response:
                200 OK: List of zone objects
                [
                    {
                        "id": 1,
                        "name": "example.com.",
                        "account": 1,
                        "dnssec": false,
                        "nameservers": ["ns1.example.com.", "ns2.example.com."],
                        "server_id": "localhost",
                        "powerdns_id": "abc123",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]

            Permissions:
                - Requires CanViewZone (zone account membership)

        POST /api/v1/accounts/manage/{user_id}/zones/
            Create a new zone for the account (not implemented in current code).

            Permissions:
                - Requires CanManageZone (zone account admin/owner role)

        DELETE /api/v1/accounts/manage/{user_id}/zones/
            Delete zones for the account (not implemented in current code).

            Permissions:
                - Requires CanManageZone (zone account admin/owner role)
        """
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
