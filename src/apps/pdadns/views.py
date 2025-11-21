
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.api.accounts.models import Account
from apps.api.dns.client import PowerDNSError
from apps.api.dns.helpers import recordUpdateHelper
from apps.api.dns.models import Zone, Record
from apps.api.dns.serializers import ZoneSerializer, RecordSerializer
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

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
        zone_account = 'None'
        if Account.objects.filter(id=zone.get('account', '')).first():
            zone_account = Account.objects.filter(id=zone.get('account', '')).first()
        zone_a = Zone(
            name=zone.get('name', ''),
            kind=zone.get('kind', Zone.ZONE_KIND_NATIVE),
            nameservers=zone.get('nameservers', []),
            server_id=zone.get('server_id', 'localhost'),
            powerdns_id=zone.get('id'),
            account=zone_account,
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
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."

    service = PowerDNSService()
    powerdns_zone = service.get_zone(zone_name)

    # Try to get zone from database
    zone = Zone.objects.filter(name=zone_name).first()

    # If zone doesn't exist in DB, try to fetch from PowerDNS
    if not zone:
        powerdns_zone = service.get_zone(zone_name)

        if not powerdns_zone:
            messages.add_message(request, messages.ERROR, f"Internal Error")
            raise Exception("Internal Error")
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

    if request.method == "POST":
        if request.POST.get('formName') == "createForm":
            recordCreate = Record(
                zone=zone,
                name=request.POST.get('name'),
                record_type=request.POST.get('record_type'),
                content=request.POST.get('content'),
                ttl=request.POST.get('ttl', '3600'),
                disabled=False,
            )
            try:
                recordCreate.full_clean()
            except ValidationError as e:
                messages.add_message(request, messages.WARNING, f"{e}")

            try:
                service.create_record(zone.name, recordCreate.name, recordCreate.record_type, recordCreate.content, recordCreate.ttl)
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")
        elif request.POST.get('formName') == "editForm":
            newRecord = Record(
                zone=zone,
                name=request.POST.get('name'),
                record_type=request.POST.get('record_type'),
                content=request.POST.get('content'),
                ttl=request.POST.get('ttl', '3600'),
                disabled=False,
            )
            oldRecord = Record(
                zone=zone,
                name=request.POST.get('old_name'),
                record_type=request.POST.get('old_record_type'),
                content=request.POST.get('old_content'),
                ttl=request.POST.get('old_ttl', '3600'),
                disabled=False,
            )
            try:
                newRecord.full_clean()
                oldRecord.full_clean()
            except ValidationError as e:
                messages.add_message(request, messages.WARNING, f"{e}")
            try:
                updated = recordUpdateHelper(zone.name, oldRecord, newRecord)
                messages.add_message(request, messages.SUCCESS, f"{updated}")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")

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