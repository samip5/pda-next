from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.api.accounts.helpers import updateAccount
from apps.api.accounts.models import Account
from apps.api.dns.models import Zone
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

@login_required
def dashboard(request):
    return render(
        request,
        "admin/test.html",
        {
            "active_tab": "admin_dash",
            "page_title": _("Admin"),
        },
    )

@login_required
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
def accounts(request):
    accountList = Account.objects.all()
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
    for account in accountList:
        account.zones = len([zone for zone in zone_instances if zone.account == account.name])
        account.members = 1
    return render(
        request,
        "admin/accounts.html",
        {
            "active_tab": "pda_accounts",
            "page_title": _("Accounts"),
            "accounts": accountList
        },
    )
@login_required
def account(request, id):
    if request.method == "POST":
        try:
            updateAccount(id, request.POST.get("name"), request.POST.get('description'), request.POST.get('contact'),
                      request.POST.get('mail'))
        except Exception as e:
            messages.add_message(request, messages.WARNING, f"{e}")

    service = PowerDNSService()
    powerdns_zones = service.get_zones("localhost")
    accountElement = Account.objects.filter(id=id).first()

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
        if accountElement.name == zone_a.account:
            zone_instances.append(zone_a)

    accountElement = Account.objects.filter(id=id).first()
    return render(
        request,
        "admin/account.html",
        {
            "active_tab": "pda_account",
            "page_title": _("Account"),
            "zones": zone_instances,
            "account": accountElement
        },
    )