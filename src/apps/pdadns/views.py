"""
API Views for PowerDNS
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models.record import Record
from .models.zone import Zone
from .serializers import RecordSerializer
from .services import PowerDNSService

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for fetching DNS records.
    
    Provides endpoints to list and retrieve records from the database.
    Records can be filtered by zone, name, record type, etc.
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
    
    @action(detail=False, methods=['get'], url_path='by-zone/(?P<zone_name>[^/]+)')
    def by_zone(self, request, zone_name=None):
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

"""
Frontend Views
"""

@login_required
def domains(request):
    return render(
        request,
        "dns/domains.html",
        {
            "active_tab": "domains",
            "page_title": _("Domains"),
            "zones":[{"domain":"cappe.fi", "type":"Native", "primary":"N/A", "account":"None", "serial":"2025112001" }]
        },
    )

@login_required
def domain(request, id):
    return render(
        request,
        "dns/domain.html",
        {
            "active_tab": "domain",
            "page_title": _("Domain"),
            "id": id,
            "rrsets":[
                {"name":"@", "type":"A", "status":"Active", "ttl":"3600", "data":"91.232.155.81" },
                {"name": "@", "type": "MX", "status": "Active", "ttl": "3600", "data": "mx2.kapsi.fi."},
                {"name": "@", "type": "AAAA", "status": "Active", "ttl": "3600", "data": "2001:67c:1be8:1337::443"}
            ]
        },
    )