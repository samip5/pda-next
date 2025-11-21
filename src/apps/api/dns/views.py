import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from .models.record import Record
from .models.zone import Zone
from .serializers import ZoneSerializer
from .serializers import RecordSerializer
from .services import PowerDNSService

logger = logging.getLogger('pda')

class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for fetching DNS zones and records.

    Provides endpoints to list and retrieve zones and records from the database.
    Records can be filtered by zone.
    """

    queryset = Record.objects.all()
    serializer_class = RecordSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned records by filtering against
        query parameters in the URL.
        """
        queryset = Record.objects.select_related('zone').all()

        # Filter by zone (by zone ID or zone name)
        zone_id = self.request.query_params.get('zone_id', None)
        zone_name = self.request.query_params.get('zone_name', None)

        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        elif zone_name:
            queryset = queryset.filter(zone__name=zone_name)

        # Filter by record name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Filter by record type
        record_type = self.request.query_params.get('type', None)
        if record_type:
            queryset = queryset.filter(record_type=record_type)

        # Filter by content
        content = self.request.query_params.get('content', None)
        if content:
            queryset = queryset.filter(content__icontains=content)

        # Filter by disabled status
        disabled = self.request.query_params.get('disabled', None)
        if disabled is not None:
            disabled_bool = disabled.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(disabled=disabled_bool)

        return queryset.order_by('zone__name', 'name', 'record_type')

    @action(detail=False, methods=['get', 'post'], url_path='zones')
    def zones(self, request):
        if request.method == 'GET':
            """
            Get all Zones.

            This endpoint fetches zones from PowerDNS API on-demand and
            returns them. If the zone doesn't exist in the database, it will
            attempt to fetch from PowerDNS.
            """
            service = PowerDNSService()
            powerdns_zones = service.get_zones("localhost")

            if not powerdns_zones:
                raise NotFound(f"Zones not found")

            # Convert PowerDNS record format to Record model instances (not saved)
            zone_instances = []
            for zone in powerdns_zones:
                zone_name = zone.get('name', '')

                zone_a = Zone(
                    name=zone_name,
                    kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
                    nameservers=zone.get('nameservers', []),
                    server_id=zone.get('server_id', 'localhost'),
                    powerdns_id=zone.get('id'),
                    account=zone.get('account', ''),
                    dnssec=zone.get('dnssec', '')
                )

                zone_instances.append(zone_a)

            serializer = ZoneSerializer(zone_instances, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            """
            Create a New zone.

            """
            zone_name = request.data.get('name', '')
            zone_type = request.data.get('type', '')
            zone_account = request.data.get('account', '')
            zone_nameservers = request.data.get('nameservers', [])
            service = PowerDNSService()
            resp = service.create_zone(zone_name=zone_name, kind=zone_type, account=zone_account,
                                       nameservers=zone_nameservers)

            return Response(resp)

    @action(detail=False, methods=['get', 'delete'], url_path='zones/(?P<zone_name>[^/]+)')
    def zone(self, request, zone_name=None):
        """
        Get zone.

        This endpoint fetches zone from PowerDNS API on-demand and
        returns them. If the zone doesn't exist in the database, it will
        attempt to fetch from PowerDNS.
        """
        if request.method == 'GET':
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
            serializer = ZoneSerializer(zone, many=False)
            return Response(serializer.data)
        elif request.method == 'DELETE':
            service = PowerDNSService()
            resp = service.delete_zone(zone_name=zone_name)
            return Response(resp)

    @action(detail=False, methods=['get', 'post'], url_path='zones/(?P<zone_name>[^/]+)/records')
    def zone_records(self, request, zone_name=None):
        if request.method == 'GET':
            """
            Get all records for a specific zone by zone name.

            This endpoint fetches records from PowerDNS API on-demand and
            returns them. If the zone doesn't exist in the database, it will
            attempt to fetch from PowerDNS.
            """
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
                return Response(400, "Error Validating record")
            service.create_record(zone.name, record.name, record.record_type, record.content, record.ttl)
            return Response(RecordSerializer(record).data)

    @action(detail=False, methods=['get', 'post', 'delete'], url_path='zones/(?P<zone_name>[^/]+)/dnssec')
    def dnssec(self, request, zone_name=None):
        service = PowerDNSService()
        if request.method == 'GET':
            # Ensure zone name has trailing dot
            if not zone_name.endswith('.'):
                zone_name = f"{zone_name}."

            # Try to get zone from database
            zone = Zone.objects.filter(name=zone_name).first()

            # If zone doesn't exist in DB, try to fetch from PowerDNS
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
            service.dnssec_records(zone.name)

            return Response('')
        elif request.method == 'POST':
            # Ensure zone name has trailing dot
            if not zone_name.endswith('.'):
                zone_name = f"{zone_name}."

            # Try to get zone from database
            zone = Zone.objects.filter(name=zone_name).first()

            # If zone doesn't exist in DB, try to fetch from PowerDNS
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
            resp = service.dnssec_keys(zone.name)

            return Response(resp)
        elif request.method == 'DELETE':
            resp = service.disable_dnssec(zone_name)
            return Response(resp)
