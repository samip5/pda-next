import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

import config
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog
from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import get_zones, get_zone, get_records
from apps.api.dns.models import Zone
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

from apps.pdaAdmin.forms import ZoneForm, AccountForm

logger = logging.getLogger('pda')
@login_required
@permission_required('pda.admin_dashboard', raise_exception=True)
def dashboard(request):
    activity_logs = Activity.objects.all()
    new_zone_form = ZoneForm()
    account_create_form = AccountForm()

    paginator = Paginator(activity_logs, 25)
    page_number = request.GET.get('page')  # get the page number from query params
    page_obj = paginator.get_page(page_number)  # returns a Page object

    return render(
        request,
        "admin/dashboard.html",
        {
            "active_tab": "admin_dash",
            "page_title": _("Admin"),
            "activity_logs": activity_logs,
            "page_obj": page_obj,
            "new_zone_form": new_zone_form,
            "account_create_form": account_create_form
        },
    )
@login_required
@permission_required('pda.admin_settings', raise_exception=True)
def settings(request):
    view_settings = {setting: getattr(config.settings, setting) for setting in dir(config.settings) if setting.isupper()}
    return render(
        request,
        "admin/settings.html",
        {
            "active_tab": "pda_settings",
            "page_title": _("Settings"),
            "settings": view_settings
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def accounts(request):
    if request.method == "POST":
        account_create_form = AccountForm(request.POST)
        if account_create_form.is_valid():
            account_create_form.save()  # creates and saves a new Account
            addActivityLog(ActionType.ACCOUNT_CREATE, f"{account_create_form.name}", request.user)
    else:
        account_create_form = AccountForm()
    accountList = Account.objects.all()
    zone_instances = get_zones()
    zone_counts = []
    member_counts = []
    for account in accountList:
        zone_counts.append({
            "account_id": account.id,
            "count": zone_instances.filter(account=account).count()
        })
        member_counts.append({
            "account_id": account.id,
            "count": account.members.count()
        })
    return render(
        request,
        "admin/accounts.html",
        {
            "active_tab": "pda_accounts",
            "page_title": _("Accounts"),
            "accounts": accountList,
            "zone_counts": zone_counts,
            "member_counts": member_counts,
            "account_create_form": account_create_form
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def account(request, id):
    account_instance = Account.objects.filter(id=id).first()
    if request.method == "POST":
        account_edit_form = AccountForm(request.POST, instance=account_instance)
        if account_edit_form.is_valid():
            account_edit_form.save()  # creates and saves a new Account
            addActivityLog(ActionType.ACCOUNT_UPDATE, f"{id}", request.user)
    else:
        account_edit_form = AccountForm(instance=account_instance)
    zone_instances = get_zones()
    filtered_zones = zone_instances.filter(account=account_instance)
    members = account_instance.members.all()
    return render(
        request,
        "admin/account.html",
        {
            "active_tab": "pda_account",
            "page_title": _("Account"),
            "zones": filtered_zones,
            "account": account_instance,
            "members": members,
            "account_edit_form": account_edit_form
        },
    )

@login_required
@permission_required('api_dns.view_zone', raise_exception=True)
def zones(request):
    service = PowerDNSService()
    accountList = Account.objects.all()

    if request.method == 'POST':
        new_zone_form = ZoneForm(request.POST)
        if new_zone_form.is_valid():
            new_zone = new_zone_form.save(commit=False)
            zone.dnssec = False
            try:
                service.create_zone(zone_name=new_zone.name, kind=new_zone.kind, account=str(new_zone.account.id),
                                   nameservers=new_zone.nameservers)
                addActivityLog(ActionType.ZONE_CREATE, f"{new_zone.name} - {new_zone.account}", request.user)
                messages.add_message(request, messages.SUCCESS, f"Zone {new_zone.name} created")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")
    new_zone_form = ZoneForm()
    zone_instances = get_zones()

    return render(
        request,
        "admin/zones.html",
        {
            "active_tab": "admin_zones",
            "page_title": _("Zones"),
            "zones":zone_instances,
            "accounts": accountList,
            "new_zone_form":new_zone_form
        },
    )

@login_required
@permission_required('api_dns.view_zone', raise_exception=True)
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
