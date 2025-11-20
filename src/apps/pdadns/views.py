
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.api.dns.models import Zone, Record
from apps.api.dns.serializers import ZoneSerializer, RecordSerializer
from apps.api.dns.services import PowerDNSService

"""
Frontend Views
"""

@login_required
def domains(request):
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


    return render(
        request,
        "dns/domains.html",
        {
            "active_tab": "domains",
            "page_title": _("Domains"),
            "zones":zone_instances
        },
    )

@login_required
def domain(request, id):
    zone_name = id

    service = PowerDNSService()
    powerdns_zone = service.get_zone(zone_name)

    powerdns_records = service.get_records(zone_name)

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
                zone=powerdns_zone.get("zone_name"),
                name=normalized_name,
                record_type=rrset_type,
                content=content,
                ttl=rrset_ttl,
                disabled=disabled,
            )
            record_instances.append(record)

    return render(
        request,
        "dns/domain.html",
        {
            "active_tab": "domain",
            "page_title": _("Domain"),
            "id": id,
            "records": record_instances
        },
    )