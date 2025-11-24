import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from apps.api.accounts.helpers import updateAccount
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog
from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import get_zones, get_zone, get_records, zone_account
from apps.api.dns.models import Zone, Record
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

logger = logging.getLogger('pda')
@login_required
@permission_required('pda.admin_dashboard', raise_exception=True)
def dashboard(request):
    activity_logs = Activity.objects.all()

    return render(
        request,
        "admin/dashboard.html",
        {
            "active_tab": "admin_dash",
            "page_title": _("Admin"),
            "activity_logs": activity_logs
        },
    )
@login_required
@permission_required('pda.admin_settings', raise_exception=True)
def settings(request):
    return render(
        request,
        "admin/settings.html",
        {
            "active_tab": "pda_settings",
            "page_title": _("Settings"),
            "settings": {}
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def accounts(request):
    accountList = Account.objects.all()
    zone_instances = get_zones()
    zone_counts = []
    for account in accountList:
        zone_counts.append({
            "account_id": account.id,
            "count": zone_instances.filter(account=account).count()
        })
        account.members = 1
    return render(
        request,
        "admin/accounts.html",
        {
            "active_tab": "pda_accounts",
            "page_title": _("Accounts"),
            "accounts": accountList,
            "zone_counts": zone_counts
        },
    )

@login_required
@permission_required('pda.admin_accounts')
def account(request, id):
    if request.method == "POST":
        try:
            updateAccount(id, request.POST.get("name"), request.POST.get('description'), request.POST.get('contact'),
                      request.POST.get('mail'))
            addActivityLog(ActionType.ACCOUNT_UPDATE, f"{id}", request.user)
        except Exception as e:
            messages.add_message(request, messages.WARNING, f"{e}")

    account_instance = Account.objects.filter(id=id).first()

    zone_instances = get_zones()
    filtered_zones = zone_instances.filter(account=account_instance)

    return render(
        request,
        "admin/account.html",
        {
            "active_tab": "pda_account",
            "page_title": _("Account"),
            "zones": filtered_zones,
            "account": account_instance
        },
    )
@login_required
@permission_required('pda.admin_zones')
def zones(request):
    service = PowerDNSService()
    accountList = Account.objects.all()

    if request.method == 'POST':
        zone_account = Account.objects.filter(id=request.POST.get('account', '')).first()
        newZone = Zone(
            name=request.POST.get('name', ''),
            kind='Native',
            account=zone_account,
            nameservers=['ns1.fuckmylife.fi.']
        )
        try:
            service.create_zone(zone_name=newZone.name, kind=newZone.kind, account=str(newZone.account.id),
                                   nameservers=newZone.nameservers)
            addActivityLog(ActionType.ZONE_CREATE, f"{newZone.name} - {newZone.account}", request.user)
            messages.add_message(request, messages.SUCCESS, f"Zone {newZone.name} created")
        except Exception as e:
            messages.add_message(request, messages.WARNING, f"{e}")

    zone_instances = get_zones()
    powerdns_zones = service.get_zones("localhost")

    # Convert PowerDNS record format to Record model instances (not saved)
    zone_instances = []
    for zone in powerdns_zones:
        zone_account = None
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
        "admin/zones.html",
        {
            "active_tab": "admin_zones",
            "page_title": _("Zones"),
            "zones":zone_instances,
            "accounts": accountList
        },
    )

@login_required
@permission_required('pda.admin_zones')
def zone(request, id):
    zone_name = id
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."

    service = PowerDNSService()
    zzone = get_zone(zone_name)
    accountList = Account.objects.all()

    for account in accountList:
        account.id_str = str(account.id)

    if request.method == "POST":
        zone_account = Account.objects.filter(id=request.POST.get('account', '')).first()
        updated_zone = Zone(
            name=zzone.name,
            account=zone_account,
            nameservers=zzone.nameservers,
            dnssec=zzone.dnssec
        )

        try:
            service.update_zone(zone_name=zone_name, account=str(updated_zone.account.id),
                                nameservers=updated_zone.nameservers,
                                dnssec=updated_zone.dnssec)
            addActivityLog(ActionType.ZONE_UPDATE, f"{zone_name} - {updated_zone.account}", request.user)
            zzone = updated_zone
        except Exception as e:
            messages.add_message(request, messages.WARNING, f"{e}")

    record_instances = get_records(zone_name)

    return render(
        request,
        "admin/zone.html",
        {
            "active_tab": "admin_zone",
            "page_title": _("Zone"),
            "zone":zzone,
            "records": record_instances,
            "accounts":accountList
        },
    )
