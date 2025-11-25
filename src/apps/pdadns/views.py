import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import recordUpdateHelper, get_zones, get_zone, get_records, delete_record
from apps.api.dns.models import Zone, Record
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

"""
Frontend Views
"""

@login_required
def domains(request):
    zone_instances = get_zones()
    accounts = Account.objects.filter(Q(members=request.user) | Q(owner=request.user))
    zone_instances = zone_instances.filter(account__in=accounts)

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
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."

    zone = get_zone(zone_name)

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
            new_record_name = recordCreate.name
            if recordCreate.name == "@":
                new_record_name = zone.name
            try:
                recordCreate.full_clean()
            except ValidationError as e:
                messages.add_message(request, messages.WARNING, f"{e}")

            try:
                addActivityLog(ActionType.RECORD_CREATE, f"{zone.name} - {recordCreate.name}", request.user)
                service.create_record(zone.name, new_record_name, recordCreate.record_type, recordCreate.content, recordCreate.ttl)
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
                updated = recordUpdateHelper(zone.name, oldRecord, newRecord)
                addActivityLog(ActionType.RECORD_UPDATE, f"{zone.name} - {newRecord.name}", request.user)
                messages.add_message(request, messages.SUCCESS, f"{updated}")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")

    record_instances = get_records(zone_name)

    return render(
        request,
        "dns/domain.html",
        {
            "active_tab": "domain",
            "page_title": _("Domain"),
            "id": id,
            "zone": zone,
            "records": record_instances
        },
    )
@login_required
@require_POST
def delete_record_view(request, id):
    zone_name = id
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."
    request.POST.get('record_type')
    zone = get_zone(zone_name)
    records = get_records(zone_name)
    record = records.filter(record_type=request.POST.get('record_type'), name=request.POST.get('name'), content=request.POST.get('content')).first()
    delete_record(zone_name=zone.name, record=record)
    addActivityLog(ActionType.RECORD_DELETE, f"{zone.name} - {record.name}", request.user)
    return redirect('pdadns:domain', id)