import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.api.decorators import MethodPermissionMixin, method_permissions
from apps.api.permissions import CanViewZone, CanManageZone

from .helpers import recordUpdateHelper
from .models.record import Record
from .models.zone import Zone
from .serializers import ZoneSerializer
from .serializers import RecordSerializer
from .services import PowerDNSService
from ..accounts.models import Account

logger = logging.getLogger('pda')

class RecordViewSet(MethodPermissionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    permission_classes = [CanViewZone]

    def get_queryset(self):
        queryset = Record.objects.select_related('zone').all()

        # Filter by zone (by zone ID or zone name)
        zone_id = getattr(self.request, 'query_params', {}).get('zone_id', None)  # type: ignore[attr-defined]
        zone_name = getattr(self.request, 'query_params', {}).get('zone_name', None)  # type: ignore[attr-defined]

        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        elif zone_name:
            queryset = queryset.filter(zone__name=zone_name)

        # Filter by record name
        name = getattr(self.request, 'query_params', {}).get('name', None)  # type: ignore[attr-defined]
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Filter by record type
        record_type = getattr(self.request, 'query_params', {}).get('type', None)  # type: ignore[attr-defined]
        if record_type:
            queryset = queryset.filter(record_type=record_type)

        # Filter by content
        content = getattr(self.request, 'query_params', {}).get('content', None)  # type: ignore[attr-defined]
        if content:
            queryset = queryset.filter(content__icontains=content)

        # Filter by disabled status
        disabled = getattr(self.request, 'query_params', {}).get('disabled', None)  # type: ignore[attr-defined]
        if disabled is not None:
            disabled_bool = str(disabled).lower() in ('true', '1', 'yes')
            queryset = queryset.filter(disabled=disabled_bool)

        return queryset.order_by('zone__name', 'name', 'record_type')

    @extend_schema(
        summary="List DNS records",
        description="List DNS records with optional filtering. Records can be filtered by zone, name, type, content, and disabled status. Results are paginated with 100 items per page.",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='zone_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter records by zone ID',
                required=False,
            ),
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter records by zone name',
                required=False,
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter records by name (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter records by record type (A, AAAA, MX, etc.)',
                required=False,
            ),
            OpenApiParameter(
                name='content',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter records by content (case-insensitive partial match)',
                required=False,
            ),
            OpenApiParameter(
                name='disabled',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by disabled status (true/false/1/0/yes)',
                required=False,
            ),
        ],
        responses={
            200: RecordSerializer,
        }
    )
    def list(self, request):
        return super().list(request)

    @extend_schema(
        summary="Retrieve a specific DNS record",
        description="Retrieve a single DNS record by ID.",
        responses={
            200: RecordSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

    @extend_schema(
        methods=['GET'],
        summary="List all zones",
        description="Get all zones. This endpoint fetches zones from PowerDNS API on-demand and returns them.",
        responses={
            200: ZoneSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['POST'],
        summary="Create a new zone",
        description="Create a new DNS zone in PowerDNS.",
        request=ZoneSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['get', 'post'], url_path='zones')
    @method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone]})
    def zones(self, request):
        if request.method == 'GET':
            service = PowerDNSService()
            powerdns_zones = service.get_zones("localhost")

            if not powerdns_zones:
                raise NotFound(f"Zones not found")

            # Convert PowerDNS record format to Record model instances (not saved)
            zone_instances = []
            for zone in powerdns_zones:
                zone_name = zone.get('name', '')
                zone_account = Account.objects.filter(id=zone.get('account', '')).first()

                zone_a = Zone(
                    name=zone_name,
                    kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
                    nameservers=zone.get('nameservers', []),
                    server_id=zone.get('server_id', 'localhost'),
                    powerdns_id=zone.get('id'),
                    account=zone_account,
                    dnssec=zone.get('dnssec', '')
                )

                zone_instances.append(zone_a)

            serializer = ZoneSerializer(zone_instances, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            zone_name = request.data.get('name', '')
            zone_type = request.data.get('type', '')
            zone_account = Account.objects.filter(id=request.data.get('account', '')).first()
            zone_nameservers = request.data.get('nameservers', [])
            service = PowerDNSService()
            resp = service.create_zone(zone_name=zone_name, kind=zone_type, account=zone_account,
                                       nameservers=zone_nameservers)

            return Response(resp)

    @extend_schema(
        methods=['GET'],
        summary="Retrieve a specific zone",
        description="Get zone details by zone name. Fetches from PowerDNS API on-demand.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        responses={
            200: ZoneSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['POST'],
        summary="Update a zone",
        description="Update zone settings (account, nameservers, DNSSEC).",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        request=ZoneSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['DELETE'],
        summary="Delete a zone",
        description="Delete a zone from PowerDNS.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='zones/(?P<zone_name>[^/]+)')
    @method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone], 'DELETE': [CanManageZone]})
    def zone(self, request, zone_name=None):
        if not zone_name.endswith('.'):
            zone_name = f"{zone_name}."

        service = PowerDNSService()
        powerdns_zone = service.get_zone(zone_name)

        if not powerdns_zone:
            raise NotFound(f"Zone '{zone_name}' not found")

        # Convert PowerDNS record format to Record model instances (not saved)

        zone = Zone(
            name=powerdns_zone.get('name', ''),
            kind=powerdns_zone.get('kind', Zone.ZONE_KIND_NATIVE),
            nameservers=powerdns_zone.get('nameservers', []),
            server_id=powerdns_zone.get('server_id', 'localhost'),
            powerdns_id=powerdns_zone.get('id'),
            account=powerdns_zone.get('account', ''),
            dnssec=powerdns_zone.get('dnssec', '')
        )
        if request.method == 'GET':
            serializer = ZoneSerializer(zone, many=False)
            return Response(serializer.data)
        elif request.method == 'POST':
            updatedZone = Zone(
                name=zone.name,
                account=request.data.get('account', zone.account),
                nameservers=request.data.get('nameservers', zone.nameservers),
                dnssec=request.data.get('dnssec', zone.dnssec)
            )

            resp = service.update_zone(zone_name=zone_name, account=updatedZone.account, nameservers=updatedZone.nameservers, dnssec=updatedZone.dnssec)
            return Response(resp)
        elif request.method == 'DELETE':
            resp = service.delete_zone(zone_name=zone_name)
            return Response(resp)

    @extend_schema(
        methods=['GET'],
        summary="List all records for a zone",
        description="Get all DNS records for a specific zone. Fetches from PowerDNS API on-demand.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        responses={
            200: RecordSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['POST'],
        summary="Create a new DNS record",
        description="Create a new DNS record in a zone.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        request=RecordSerializer,
        responses={
            200: RecordSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['get', 'post'], url_path='zones/(?P<zone_name>[^/]+)/records')
    #@method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone]})
    def zone_records(self, request, zone_name=None):
        if request.method == 'GET':
            # Ensure zone name has trailing dot
            if not zone_name.endswith('.'):
                zone_name = f"{zone_name}."

            # Try to get zone from database
            zone = Zone.objects.filter(name=zone_name).first()

            # If zone doesn't exist in DB, try to fetch from PowerDNS
            if not zone:
                service = PowerDNSService()
                powerdns_zone = service.get_zone(zone_name)

                if not powerdns_zone:
                    raise NotFound(f"Zone '{zone_name}' not found")

                # Create zone in database for reference
                zone = Zone.objects.create(
                    name=zone_name,
                    kind=powerdns_zone.get('kind', Zone.ZONE_KIND_NATIVE),
                    nameservers=powerdns_zone.get('nameservers', []),
                    server_id=powerdns_zone.get('server_id', 'localhost'),
                    account=powerdns_zone.get('account', ''),
                    dnssec=powerdns_zone.get('dnssec', ''),
                    powerdns_id=powerdns_zone.get('id')
                )

            # Fetch records from PowerDNS
            service = PowerDNSService()
            powerdns_records = service.get_records(zone_name, zone.server_id)

            # Convert PowerDNS record format to Record model instances (not saved)
            record_instances = []
            for rrset in powerdns_records:
                rrset_name = rrset.get('name', '')
                rrset_type = rrset.get('type', '')
                rrset_ttl = rrset.get('ttl', 3600)

                for record_data in rrset.get('records', []):
                    content = record_data.get('content', '')
                    disabled = record_data.get('disabled', False)

                    # Normalize name (remove zone suffix if present)
                    normalized_name = rrset_name
                    if normalized_name.endswith('.'):
                        normalized_name = normalized_name.rstrip('.')
                    zone_name_clean = zone_name.rstrip('.')
                    if normalized_name == zone_name_clean:
                        normalized_name = '@'
                    elif normalized_name.endswith(f".{zone_name_clean}"):
                        normalized_name = normalized_name[:-len(f".{zone_name_clean}")]

                    # Create Record instance in memory (not saved to DB)
                    record = Record(
                        zone=zone,
                        name=normalized_name,
                        record_type=rrset_type,
                        content=content,
                        ttl=rrset_ttl,
                        disabled=disabled,
                    )
                    record_instances.append(record)

            serializer = RecordSerializer(record_instances, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            service = PowerDNSService()
            if not zone_name.endswith('.'):
                zone_name = f"{zone_name}."

            zone = Zone.objects.filter(name=zone_name).first()
            if not zone:
                powerdns_zone = service.get_zone(zone_name)

                if not powerdns_zone:
                    raise NotFound(f"Zone '{zone_name}' not found")

                # Create zone in database for reference
                zone = Zone.objects.create(
                    name=zone_name,
                    kind=powerdns_zone.get('kind', Zone.ZONE_KIND_NATIVE),
                    nameservers=powerdns_zone.get('nameservers', []),
                    server_id=powerdns_zone.get('server_id', 'localhost'),
                    account=powerdns_zone.get('account', ''),
                    dnssec=powerdns_zone.get('dnssec', ''),
                    powerdns_id=powerdns_zone.get('id')
                )

            record = Record(
                zone=zone,
                name=request.data.get('name'),
                record_type=request.data.get('record_type'),
                content=request.data.get('content'),
                ttl=request.data.get('ttl', '3600'),
                disabled=request.data.get('disabled', 'false'),
            )

            try:
                record.full_clean()
            except ValidationError as e:
                return Response("Error Validating record", 400)
            service.create_record(zone.name, record.name, record.record_type, record.content, record.ttl)
            return Response(RecordSerializer(record).data)

    @extend_schema(
        methods=['GET'],
        summary="Get records by name",
        description="Get all DNS records with a specific name in a zone.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
            OpenApiParameter(
                name='record_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Record name (e.g., "www" or "@" for zone apex)',
                required=True,
            ),
        ],
        responses={
            200: RecordSerializer,
            404: {},
        }
    )
    @extend_schema(
        methods=['POST'],
        summary="Update a DNS record",
        description="Update an existing DNS record. Requires old_record_type if multiple records exist with the same name.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
            OpenApiParameter(
                name='record_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Record name (e.g., "www" or "@" for zone apex)',
                required=True,
            ),
        ],
        request=RecordSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['DELETE'],
        summary="Delete a DNS record",
        description="Delete a DNS record from a zone. Requires record_type in request body.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
            OpenApiParameter(
                name='record_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Record name (e.g., "www" or "@" for zone apex)',
                required=True,
            ),
        ],
        request=RecordSerializer,
        responses={
            200: OpenApiTypes.STR,
            404: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['get', 'post','delete'], url_path='zones/(?P<zone_name>[^/]+)/records/(?P<record_id>[^/]+)')
    #@method_permissions({'GET': [CanViewZone], 'POST': [CanManageZone], 'DELETE': [CanManageZone]})
    def zone_record(self, request, zone_name=None, record_id=None):
        service = PowerDNSService()
        # Ensure zone name has trailing dot
        if not zone_name.endswith('.'):
            zone_name = f"{zone_name}."

        # Try to get zone from database
        zone = Zone.objects.filter(name=zone_name).first()

        # If zone doesn't exist in DB, try to fetch from PowerDNS
        if not zone:
            service = PowerDNSService()
            powerdns_zone = service.get_zone(zone_name)

            if not powerdns_zone:
                raise NotFound(f"Zone '{zone_name}' not found")

            # Create zone in database for reference
            zone = Zone.objects.create(
                name=zone_name,
                kind=powerdns_zone.get('kind', Zone.ZONE_KIND_NATIVE),
                nameservers=powerdns_zone.get('nameservers', []),
                server_id=powerdns_zone.get('server_id', 'localhost'),
                account=powerdns_zone.get('account', ''),
                dnssec=powerdns_zone.get('dnssec', ''),
                powerdns_id=powerdns_zone.get('id')
            )

        # Fetch records from PowerDNS
        powerdns_records = service.get_records(zone_name, zone.server_id)

        # Convert PowerDNS record format to Record model instances (not saved)
        record_instances = []
        for rrset in powerdns_records:
            rrset_name = rrset.get('name', '')
            rrset_type = rrset.get('type', '')
            rrset_ttl = rrset.get('ttl', 3600)

            for record_data in rrset.get('records', []):
                content = record_data.get('content', '')
                disabled = record_data.get('disabled', False)

                # Normalize name (remove zone suffix if present)
                normalized_name = rrset_name
                if normalized_name.endswith('.'):
                    normalized_name = normalized_name.rstrip('.')
                zone_name_clean = zone_name.rstrip('.')
                if normalized_name == zone_name_clean:
                    normalized_name = '@'
                elif normalized_name.endswith(f".{zone_name_clean}"):
                    normalized_name = normalized_name[:-len(f".{zone_name_clean}")]

                # Create Record instance in memory (not saved to DB)
                record = Record(
                    zone=zone,
                    name=normalized_name,
                    record_type=rrset_type,
                    content=content,
                    ttl=rrset_ttl,
                    disabled=disabled,
                )
                record_instances.append(record)

        if request.method == 'GET':
            matching_records = [r for r in record_instances if r.name.lower() == record_id.lower()]
            serializer = RecordSerializer(matching_records, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            matching_records = []
            if request.data.get('old_record_type'):
                matching_records = [
                r for r in record_instances
                if r.name == record_id and r.record_type == request.data.get('old_record_type')]
            else:
                matching_records = [
                r for r in record_instances
                if r.name == record_id and r.record_type == request.data.get('record_type')]

            try:
                old_record = matching_records[0]
            except IndexError:
                return Response("Record not found", 404)

            new_record = Record(
                zone=zone,
                name=request.data.get('name'),
                record_type=request.data.get('record_type'),
                content=request.data.get('content'),
                ttl=request.data.get('ttl'),
                disabled=request.data.get('disabled'),
            )
            try:
                response = recordUpdateHelper(zone.name, old_record, new_record)
                return Response(response)
            except Exception as e:
                return Response(str(e), 500)
        elif request.method == 'DELETE':

            matching_records = [
                r for r in record_instances
                if r.name == record_id and r.record_type == request.data.get('record_type')]

            try:
                oldRecord = matching_records[0]
                service.delete_record(zone_name, oldRecord.name, oldRecord.record_type, oldRecord.content)
                return Response("Record Deleted", 200)
            except IndexError:
                return Response("Record not found", 404)

    @extend_schema(
        methods=['POST'],
        summary="Enable DNSSEC for a zone",
        description="Generate and enable DNSSEC keys for a zone.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    @extend_schema(
        methods=['DELETE'],
        summary="Disable DNSSEC for a zone",
        description="Disable DNSSEC for a zone.",
        parameters=[
            OpenApiParameter(
                name='zone_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Zone name (with or without trailing dot)',
                required=True,
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['post', 'delete'], url_path='zones/(?P<zone_name>[^/]+)/dnssec')
    @method_permissions({'POST': [CanManageZone], 'DELETE': [CanManageZone]})
    def dnssec(self, request, zone_name=None):
        service = PowerDNSService()
        if request.method == 'POST':
            resp = service.dnssec_keys(zone_name)
            return Response(resp)
        elif request.method == 'DELETE':
            resp = service.disable_dnssec(zone_name)
            return Response(resp)
