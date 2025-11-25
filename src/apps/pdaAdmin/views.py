import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django_auth_ldap.config import LDAPSearch

import config
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog
from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import get_zones, get_zone, get_records, create_zone_from_template, delete_zone, \
    recordUpdateHelper
from apps.api.dns.models import Zone, Record
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

from apps.api.templates.models import ZoneTemplate, RecordTemplate, zone_template
from apps.globalSettings.utils import get_setting, set_setting
from apps.pdaAdmin.forms import ZoneForm, AccountForm, ZoneTemplateForm, RecordTemplateForm, CreateZoneForm, UserForm, \
    UserPermissionsForm, UserGroupsForm, GroupForm, GroupPermissionsForm
from apps.users.models import CustomUser
from config import load_db_settings_to_config, save_config
from config.settings import app_settings

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
    ldap_settings = {
        "auth_ldap_start_tls": f"{get_setting('auth_ldap_start_tls')}",
        "auth_ldap_server_uri": f"{get_setting('auth_ldap_server_uri')}",
        "auth_ldap_bind_dn": f"{get_setting('auth_ldap_bind_dn')}",
        "auth_ldap_bind_password": f"{get_setting('auth_ldap_bind_password')}",
        "auth_ldap_create_users": f"{get_setting('auth_ldap_create_users')}",
        "auth_ldap_user_search_base": f"{get_setting('auth_ldap_user_search_base')}",
        "auth_ldap_user_search_filter": f"{get_setting('auth_ldap_user_search_filter')}"
    }
    record_types = Record.RECORD_TYPE_CHOICES
    setting_record_types = get_setting('record_types')

    if request.method == "POST":
        form_type = request.POST.get('form_type')
        if form_type == "ldap":
            for key in ldap_settings:
                logger.info(f'{key} {request.POST.get(key)}')
                set_setting(key, request.POST.get(key))
                ldap_settings[key] = request.POST.get(key)
            load_db_settings_to_config(app_settings)
        if form_type == "record_types":
            for record_type, i in record_types:
                is_active = record_type in request.POST
                setting_record_types[record_type] = is_active
                logger.info(f'{record_type} {setting_record_types[record_type]}')
            set_setting('record_types', setting_record_types, 'json')
    view_settings = []
    view_settings.append({"name": "disable_landing_page", "value": f"{get_setting('disable_landing_page')}"})
    return render(
        request,
        "admin/settings.html",
        {
            "active_tab": "pda_settings",
            "page_title": _("Settings"),
            "settings": view_settings,
            "ldap_settings": ldap_settings,
            "record_types": record_types,
            "setting_record_types": setting_record_types
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
        new_zone_form = CreateZoneForm(request.POST)
        if new_zone_form.is_valid():
            new_zone = new_zone_form.save(commit=False)
            zone.dnssec = False
            try:
                create_zone_from_template(new_zone, template=new_zone_form.data["template"])
                addActivityLog(ActionType.ZONE_CREATE, f"{new_zone.name} - {new_zone.account}", request.user)
                messages.add_message(request, messages.SUCCESS, f"Zone {new_zone.name} created")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")
    new_zone_form = CreateZoneForm()
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
@require_POST
def delete_zone_view(request, id):
    zone = get_zone(id)
    delete_zone(zone_name=zone.name)
    addActivityLog(ActionType.ZONE_DELETE, f"{zone.name} - {zone.account}", request.user)
    return redirect('pdaAdmin:zones')

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
        form_type = request.POST.get('form_type')
        if form_type == 'zone':
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
        if form_type == "recordEdit":
            newRecord = Record(
                zone=zzone,
                name=request.POST.get('name'),
                record_type=request.POST.get('record_type'),
                content=request.POST.get('content'),
                ttl=request.POST.get('ttl', '3600'),
                disabled=False,
            )
            oldRecord = Record(
                zone=zzone,
                name=request.POST.get('old_name'),
                record_type=request.POST.get('old_record_type'),
                content=request.POST.get('old_content'),
                ttl=request.POST.get('old_ttl', '3600'),
                disabled=False,
            )
            try:
                updated = recordUpdateHelper(zzone.name, oldRecord, newRecord)
                addActivityLog(ActionType.RECORD_UPDATE, f"({newRecord.record_type}) {newRecord.name} - {zzone.name} updated", request.user)
                messages.add_message(request, messages.SUCCESS, f"{updated}")
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


@login_required
@permission_required('api_templates.view_zonetemplate', raise_exception=True)
def templates(request):
    if request.method == "POST":
        zone_template_form = ZoneTemplateForm(request.POST)
        if zone_template_form.is_valid():
            zone_template_form.save()
            addActivityLog(ActionType.TEMPLATE_CREATE, f"{zone_template_form.data['name']}", request.user)
    else:
        zone_template_form = ZoneTemplateForm()
    zone_templates = ZoneTemplate.objects.all()
    return render(
        request,
        "admin/templates/index.html",
        {
            "active_tab": "templates",
            "page_title": _("Templates"),
            "templates": zone_templates,
            "zone_template_form":zone_template_form
        },
    )

@login_required
@permission_required('api_templates.add_zonetemplate', raise_exception=True)
def edit_template(request, id):
    template = ZoneTemplate.objects.get(id=id)
    template_records = RecordTemplate.objects.filter(zone_template=template)
    if request.method == "POST":
        record_template_form = RecordTemplateForm(request.POST)
        zone_template_form = ZoneTemplateForm(request.POST, instance=template)

        if record_template_form.is_valid():
            record_template = record_template_form.save(commit=False)
            record_template.zone_template = template
            record_template.save()
            addActivityLog(ActionType.TEMPLATE_RECORD_CREATE, f"{record_template_form.data['name']}", request.user)
            return redirect("pdaAdmin:edit_template", id)
        if zone_template_form.is_valid():
            zone_template_form.save()
            addActivityLog(ActionType.TEMPLATE_UPDATE, f"{zone_template_form.data['name']}", request.user)
            return redirect("pdaAdmin:edit_template", id)

    else:
        record_template_form = RecordTemplateForm()
        zone_template_form = ZoneTemplateForm(instance=template)

    return render(
        request,
        "admin/templates/edit.html",
        {
            "active_tab": "templates_create",
            "page_title": _("Zone"),
            "template":template,
            "template_records":template_records,
            "zone_template_form": zone_template_form,
            "record_template_form": record_template_form
        },
    )

@login_required
@require_POST
def clear_cache(request):
    if request.user.is_superuser:
        Zone.objects.all().delete()
        Record.objects.all().delete()
        addActivityLog(ActionType.CLEAR_CACHE, f"Clearing Zone and Record Cache's", request.user)
        return redirect('pdaAdmin:dashboard')
    return redirect('pdaAdmin:dashboard')

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def users(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            user_form.save()  # creates and saves a new Account
            addActivityLog(ActionType.USER_CREATE, f"{user_form.data['username']}", request.user)
    else:
        user_form = UserForm()
    users = CustomUser.objects.all()

    return render(
        request,
        "admin/users.html",
        {
            "active_tab": "pda_users",
            "page_title": _("Accounts"),
            "users": users,
            "user_form": user_form
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def user(request, id):
    _user = CustomUser.objects.get(id=id)
    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == 'user':
            user_form = UserForm(request.POST, instance=_user)
            if user_form.is_valid():
                user_form.save()  # creates and saves a new Account
                addActivityLog(ActionType.USER_CREATE, f"{user_form.data['username']}", request.user)
                return redirect("pdaAdmin:user", id)
        if form_type == 'permissions':
            user_permission_form = UserPermissionsForm(request.POST, instance=_user)
            if user_permission_form.is_valid():
                user_permission_form.save()  # creates and saves a new Account
                addActivityLog(ActionType.USER_UPDATE, f"Permissions updated for {_user.username}", request.user)
                return redirect("pdaAdmin:user", id)
        if form_type == 'groups':
            user_groups_form = UserGroupsForm(request.POST, instance=_user)
            if user_groups_form.is_valid():
                user_groups_form.save()  # creates and saves a new Account
                addActivityLog(ActionType.USER_UPDATE, f"Groups updated for {_user.username}", request.user)
                return redirect("pdaAdmin:user", id)
    else:
        user_form = UserForm(instance=_user)
        user_permission_form = UserPermissionsForm(instance=_user)
        user_groups_form = UserGroupsForm(instance=_user)

    return render(
        request,
        "admin/user.html",
        {
            "active_tab": "pda_user",
            "page_title": _("Account"),
            "user": _user,
            "user_form": user_form,
            "user_permission_form":user_permission_form,
            "user_groups_form":user_groups_form
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def groups(request):
    if request.method == "POST":
        group_form = GroupForm(request.POST)
        if group_form.is_valid():
            group_form.save()  # creates and saves a new Account
            addActivityLog(ActionType.GROUP_CREATE, f"{group_form.data['name']}", request.user)
    else:
        group_form = GroupForm()
    _groups = Group.objects.all()

    return render(
        request,
        "admin/groups.html",
        {
            "active_tab": "pda_groups",
            "page_title": _("Accounts"),
            "groups": _groups,
            "group_form": group_form
        },
    )

@login_required
@permission_required('pda.admin_accounts', raise_exception=True)
def group(request, id):
    _group = Group.objects.get(id=id)
    if request.method == "POST":
        form_type = request.POST.get('form_type')
        if form_type == 'group':
            group_form = GroupForm(request.POST, instance=_group)
            if group_form.is_valid():
                group_form.save()
                addActivityLog(ActionType.GROUP_UPDATE, f"{group_form.data['username']}", request.user)
                return redirect("pdaAdmin:group", id)
        if form_type == 'permissions':
            group_permission_form = GroupPermissionsForm(request.POST, instance=_group)
            if group_permission_form.is_valid():
                group_permission_form.save()
                addActivityLog(ActionType.USER_UPDATE, f"Permissions updated for {_group.name}", request.user)
                return redirect("pdaAdmin:group", id)
    else:
        group_form = GroupForm(instance=_group)
        group_permission_form = GroupPermissionsForm(instance=_group)

    return render(
        request,
        "admin/group.html",
        {
            "active_tab": "pda_group",
            "page_title": _("Account"),
            "group": _group,
            "group_form": group_form,
            "group_permission_form":group_permission_form,
        },
    )
