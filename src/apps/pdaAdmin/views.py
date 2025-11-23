from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.api.accounts.helpers import updateAccount
from apps.api.accounts.models import Account
from apps.api.dns.models import Zone, Record
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
        account.zones = len([zone for zone in zone_instances if zone.account == str(account.id)])
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
        if str(accountElement.id) == zone_a.account:
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

@login_required
def zones(request):
    service = PowerDNSService()
    accountList = Account.objects.all()

    if request.method == 'POST':
        newZone = Zone(
            name=request.POST.get('name', ''),
            kind='Native',
            account=request.POST.get('account', ''),
            nameservers=['ns1.fuckmylife.fi.']
        )
        try:
            service.create_zone(zone_name=newZone.name, kind=newZone.kind, account=newZone.account,
                                   nameservers=newZone.nameservers)
            messages.add_message(request, messages.SUCCESS, f"Zone {newZone.name} created")
        except Exception as e:
            messages.add_message(request, messages.WARNING, f"{e}")

    powerdns_zones = service.get_zones("localhost")

    # Convert PowerDNS record format to Record model instances (not saved)
    zone_instances = []
    for zone in powerdns_zones:
        zone_account = 'None'
        if zone.get('account', '') != '' and Account.objects.filter(id=zone.get('account', '')).first():
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
        "admin/zones.html",
        {
            "active_tab": "admin_zones",
            "page_title": _("Zones"),
            "zones":zone_instances,
            "accounts": accountList
        },
    )

@login_required
def zone(request, id):
    zone_name = id
    if not zone_name.endswith('.'):
        zone_name = f"{zone_name}."

    service = PowerDNSService()
    powerdns_zone = service.get_zone(zone_name)
    accountList = Account.objects.all()

    for account in accountList:
        account.id_str = str(account.id)

    zone = Zone(
        name=zone_name,
        kind=powerdns_zone.get('kind', Zone.ZONE_KIND_NATIVE),
        nameservers=powerdns_zone.get('nameservers', []),
        server_id=powerdns_zone.get('server_id', 'localhost'),
        account=powerdns_zone.get('account', ''),
        dnssec=powerdns_zone.get('dnssec', ''),
        powerdns_id=powerdns_zone.get('id')
    )
    if request.method == "POST":
        updatedZone = Zone(
            name=zone.name,
            account=request.POST.get('account', zone.account),
            nameservers=zone.nameservers,
            dnssec=zone.dnssec
        )

        try:
            service.update_zone(zone_name=zone_name, account=updatedZone.account,
                                nameservers=updatedZone.nameservers,
                                dnssec=updatedZone.dnssec)
            zone = updatedZone
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
        "admin/zone.html",
        {
            "active_tab": "admin_zone",
            "page_title": _("Zone"),
            "zone":zone,
            "records": record_instances,
            "accounts":accountList
        },
    )
