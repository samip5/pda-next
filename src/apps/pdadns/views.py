import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog, mergeActivityDetails, getFieldDetails
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import recordUpdateHelper, get_zones, get_zone, get_records, delete_record, create_record
from apps.api.dns.models import Zone, Record
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

from apps.globalSettings.utils import get_setting

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
    setting_record_types = get_setting('record_types')

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
                details_fields = {
                    "zone": zone.name,
                    "name": recordCreate.name,
                    "type": recordCreate.record_type,
                    "content": recordCreate.content,
                    "ttl": recordCreate.ttl,
                }
                details = mergeActivityDetails(getFieldDetails(details_fields))

                addActivityLog(ActionType.RECORD_CREATE, f"({recordCreate.record_type}) {recordCreate.name} - {zone.name} created", details, request.user)
                create_record(zone, new_record_name, recordCreate.record_type, recordCreate.content, recordCreate.ttl)
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
                details_fields = {
                    "zone": zone.name,
                    "old_name": oldRecord.name,
                    "new_name": newRecord.name,
                    "old_type": oldRecord.record_type,
                    "new_type": newRecord.record_type,
                    "old_content": oldRecord.content,
                    "new_content": newRecord.content,
                    "old_ttl": oldRecord.ttl,
                    "new_ttl": newRecord.ttl,
                }
                details = mergeActivityDetails(getFieldDetails(details_fields))

                addActivityLog(ActionType.RECORD_UPDATE, f"({newRecord.record_type}) {newRecord.name} - {zone.name} updated", details, request.user)
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
            "records": record_instances,
            "setting_record_types": setting_record_types,
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
    details_fields = {
        "zone": zone.name,
        "name": record.name,
        "type": record.record_type,
        "content": record.content,
        "ttl": record.ttl,
    }
    details = mergeActivityDetails(getFieldDetails(details_fields))
    addActivityLog(ActionType.RECORD_DELETE, f"({record.record_type}) {record.name} - {zone.name} deleted", details, request.user)
    return redirect('pdadns:domain', id)