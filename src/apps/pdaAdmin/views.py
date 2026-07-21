import logging
import uuid

from allauth.socialaccount.models import SocialApp
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django_auth_ldap.config import LDAPSearch
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.db.models import Q
import config
from apps.api.accounts.models import Account
from apps.api.activity.helpers import addActivityLog, mergeActivityDetails, getSingleUserDetails, getFieldDetails, \
    getMemberDetails, getPermissionDetails, getGroupDetails
from apps.api.activity.models import Activity
from apps.api.activity.models.activity import ActionType
from apps.api.dns.helpers import get_zones, get_zone, get_records, create_zone_from_template, delete_zone, \
    recordUpdateHelper, create_record, validate_record
from apps.api.dns.models import Zone, Record
from apps.api.dns.services import PowerDNSService
from django.contrib import messages

from apps.api.templates.models import ZoneTemplate, RecordTemplate, zone_template
from apps.globalSettings.utils import get_setting, set_setting
from apps.pdaAdmin.forms import ZoneForm, AccountForm, ZoneTemplateForm, RecordTemplateForm, CreateZoneForm, UserForm, \
    UserPermissionsForm, UserGroupsForm, GroupForm, GroupPermissionsForm, SocialAppForm
from apps.users.models import CustomUser
from config import load_db_settings_to_config, save_config
from config.settings import app_settings

@login_required
@permission_required('pdaAdmin.dashboard', raise_exception=True)
def dashboard(request):
    activity_logs = Activity.objects.all()
    new_zone_form = ZoneForm()
    account_create_form = AccountForm()

    stats = {
        "accounts": Account.objects.count(),
        "users": CustomUser.objects.count(),
        "zones": Zone.objects.count(),
    }

    paginator = Paginator(activity_logs, 25)
    page_number = request.GET.get('page')  # get the page number from query params
    page_obj = paginator.get_page(page_number)  # returns a Page object

    return render(
        request,
        "web/app/admin/dashboard.html",
        {
            "active_tab": "admin_dash",
            "page_title": _("Admin"),
            "activity_logs": activity_logs,
            "page_obj": page_obj,
            "new_zone_form": new_zone_form,
            "account_create_form": account_create_form,
            "stats": stats
        },
    )
@login_required
@permission_required('pdaAdmin.settings', raise_exception=True)
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
    social_app_form = SocialAppForm()
    if request.method == "POST":
        form_type = request.POST.get('form_type')
        if form_type == "ldap":
            for key in ldap_settings:
                set_setting(key, request.POST.get(key))
                ldap_settings[key] = request.POST.get(key)
            load_db_settings_to_config(app_settings)
        if form_type == "record_types":
            for record_type, i in record_types:
                is_active = record_type in request.POST
                setting_record_types[record_type] = is_active
            set_setting('record_types', setting_record_types, 'json')
        if form_type == "social":
            try:
                social_app_form = SocialAppForm(request.POST)
                if SocialApp.objects.filter(provider=request.POST.get('provider')).exists():
                    messages.add_message(request, messages.ERROR, f"A social app with provider '{request.POST.get('provider')}' already exists.")
                elif social_app_form.is_valid():
                    social_app_form.clean()
                    inst = social_app_form.save()
                    messages.add_message(request, messages.SUCCESS, f"Added {social_app_form.fields['name']}")
                    social_app_form = SocialAppForm()
                else:
                    messages.add_message(request, messages.WARNING, f"{social_app_form.errors.as_data()}")
            except Exception as e:
                messages.add_message(request, messages.ERROR, f"{e}")

    social_apps = SocialApp.objects.all()
    view_settings = []
    view_settings.append({"name": "disable_landing_page", "value": f"{get_setting('disable_landing_page')}"})
    view_settings.append({"name": "db_path", "value": f"{get_setting('db_path')}"})

    return render(
        request,
        "web/app/admin/settings.html",
        {
            "active_tab": "pda_settings",
            "page_title": _("Settings"),
            "settings": view_settings,
            "ldap_settings": ldap_settings,
            "record_types": record_types,
            "setting_record_types": setting_record_types,
            "social_app_form": social_app_form,
            "social_apps": social_apps
        },
    )

@login_required
@permission_required('pdaAdmin.accounts_delete', raise_exception=True)
@require_POST
def delete_account_view(request, id):
    account_instance = Account.objects.filter(id=id).first()
    account_instance.delete()
    details_fields = {
        "name": account_instance.name,
        "mail": account_instance.mail,
        "owner": account_instance.owner
    }
    details = mergeActivityDetails(getFieldDetails(details_fields))
    addActivityLog(ActionType.ACCOUNT_DELETE, f"{account_instance.name}", details, request.user)

    return redirect('pdaAdmin:accounts')

@login_required
@permission_required('pdaAdmin.accounts_view', raise_exception=True)
def accounts(request):
    if request.method == "POST":
        account_create_form = AccountForm(request.POST)
        if account_create_form.is_valid():
            account_instance = account_create_form.save()  # creates and saves a new Account
            new_members = set(account_instance.members.values_list("id", flat=True))
            new_fields = {
                "name": account_instance.name,
                "mail": account_instance.mail,
                "contact": account_instance.contact,
                "description": account_instance.description
            }
            new_owner = account_instance.owner
            print(f"new_owner: {new_owner}")
            details = mergeActivityDetails(
                getFieldDetails(new_fields),
                getSingleUserDetails("Owner", new_owner.id),
                getMemberDetails(new_members)
            )
            addActivityLog(ActionType.ACCOUNT_CREATE, f"{account_create_form.data['name']}", details, request.user)
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
        "web/app/admin/accounts/index.html",
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
@permission_required('pdaAdmin.accounts_view', raise_exception=True)
def account(request, id):
    account_instance = Account.objects.filter(id=id).first()
    if request.method == "POST":
        account_edit_form = AccountForm(request.POST, instance=account_instance)
        old_members = set(account_instance.members.values_list("id", flat=True))
        old_fields = {
            "name": account_instance.name,
            "mail": account_instance.mail,
            "contact": account_instance.contact,
            "description": account_instance.description
        }
        old_owner = account_instance.owner
        if account_edit_form.is_valid():
            account_edit_form.save()
            new_members = set(account_instance.members.values_list("id", flat=True))
            new_fields = {
                "name": account_instance.name,
                "mail": account_instance.mail,
                "contact": account_instance.contact,
                "description": account_instance.description
            }
            new_owner = account_instance.owner

            details = mergeActivityDetails(
                getFieldDetails(new_fields, old_fields),
                getSingleUserDetails("Owner", new_owner.id, old_owner.id),
                getMemberDetails(new_members, old_members))
            addActivityLog(ActionType.ACCOUNT_UPDATE, f"{id}", details, request.user)
    else:
        account_edit_form = AccountForm(instance=account_instance)
    zone_instances = get_zones()
    filtered_zones = zone_instances.filter(account=account_instance)
    members = account_instance.members.all()
    return render(
        request,
        "web/app/admin/accounts/edit.html",
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
@permission_required('pdaAdmin.zones_view', raise_exception=True)
def zones(request):
    accountList = Account.objects.all()

    if request.method == 'POST':
        new_zone_form = CreateZoneForm(request.POST)
        if new_zone_form.is_valid():
            new_zone = new_zone_form.save(commit=False)
            zone.dnssec = False
            try:
                new_fields = {
                    "name": new_zone.name,
                    "account": new_zone.account,
                    "dnssec": new_zone.dnssec,
                    "template": new_zone_form.data["template"]
                }
                details = mergeActivityDetails(getFieldDetails(new_fields))
                addActivityLog(ActionType.ZONE_CREATE, f"{new_zone.name} - {new_zone.account}", details, request.user)

                if new_zone_form.data["template"] != "":
                    create_zone_from_template(new_zone, template=new_zone_form.data["template"])
                    messages.add_message(request, messages.SUCCESS, f"Zone {new_zone.name} created")
                else :
                    create_zone_from_template(new_zone, template=None)
                    messages.add_message(request, messages.SUCCESS, f"Zone {new_zone.name} created")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")
    new_zone_form = CreateZoneForm()
    zone_instances = get_zones()

    return render(
        request,
        "web/app/admin/zones/index.html",
        {
            "active_tab": "admin_zones",
            "page_title": _("Zones"),
            "zones":zone_instances,
            "accounts": accountList,
            "new_zone_form":new_zone_form
        },
    )

@login_required
@permission_required('pdaAdmin.zones_delete', raise_exception=True)
@require_POST
def delete_zone_view(request, id):
    zone = get_zone(id)
    delete_zone(zone_name=zone.name)
    details_fields = {
        "name": zone.name,
        "account": zone.account
    }
    details = mergeActivityDetails(getFieldDetails(details_fields))
    addActivityLog(ActionType.ZONE_DELETE, f"{zone.name} - {zone.account}", details, request.user)
    return redirect('pdaAdmin:zones')

@login_required
@permission_required('pdaAdmin.zones_view', raise_exception=True)
def zone(request, id):
    zone_name = id
    setting_record_types = get_setting('record_types')

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
            zone_account = None
            zone_account_id = None
            if _is_valid_uuid(request.POST.get('account', '')):
                zone_account = Account.objects.filter(id=request.POST.get('account', '')).first()
                zone_account_id = str(zone_account.id)

            updated_zone = Zone(
                name=zzone.name,
                account=zone_account,
                nameservers=zzone.nameservers,
                dnssec=zzone.dnssec
            )
            try:
                service.update_zone(zone_name=zone_name, account=zone_account_id,
                                    nameservers=updated_zone.nameservers,
                                    dnssec=updated_zone.dnssec)
                details_fields = {
                    "name": zzone.name,
                    "updated_name": updated_zone.name,
                    "account": zzone.account,
                    "updated_account": updated_zone.account,
                    "dnssec": zzone.dnssec,
                    "updated_dnssec": updated_zone.dnssec
                }
                details = mergeActivityDetails(getFieldDetails(details_fields))
                addActivityLog(ActionType.ZONE_UPDATE, f"{zone_name} - {updated_zone.account}", details, request.user)
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
                if newRecord.record_type in ["A", "AAAA", "CNAME", "NS"]:
                    validate_record(newRecord)

                updated = recordUpdateHelper(zzone.name, oldRecord, newRecord)
                details_fields = {
                    "zone": zzone.name,
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
                addActivityLog(ActionType.RECORD_UPDATE, f"({newRecord.record_type}) {newRecord.name} - {zzone.name} updated", details, request.user)
                messages.add_message(request, messages.SUCCESS, f"{updated}")
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")
        if form_type == "recordCreate":
            recordCreate = Record(
                zone=zzone,
                name=request.POST.get('name'),
                record_type=request.POST.get('record_type'),
                content=request.POST.get('content'),
                ttl=request.POST.get('ttl', '3600'),
                disabled=False,
            )
            new_record_name = recordCreate.name
            if recordCreate.name == "@":
                new_record_name = zzone.name

            try:
                recordCreate.full_clean()
                if recordCreate.record_type in ["A", "AAAA", "CNAME", "NS"]:
                    validate_record(recordCreate)

                details_fields = {
                    "zone": zzone.name,
                    "name": recordCreate.name,
                    "type": recordCreate.record_type,
                    "content": recordCreate.content,
                    "ttl": recordCreate.ttl,
                }

                details = mergeActivityDetails(getFieldDetails(details_fields))
                addActivityLog(ActionType.RECORD_CREATE, f"({recordCreate.record_type}) {recordCreate.name} - {zzone.name} created", details, request.user)
                create_record(zzone, new_record_name, recordCreate.record_type, recordCreate.content, recordCreate.ttl)
            except Exception as e:
                messages.add_message(request, messages.WARNING, f"{e}")

    record_instances = get_records(zone_name)

    return render(
        request,
        "web/app/admin/zones/edit.html",
        {
            "active_tab": "admin_zone",
            "page_title": _("Zone"),
            "zone":zzone,
            "setting_record_types": setting_record_types,
            "records": record_instances,
            "accounts":accountList
        },
    )

@login_required
@permission_required('pdaAdmin.templates_delete', raise_exception=True)
@require_POST
def delete_template_view(request, id):
    template_instance = ZoneTemplate.objects.filter(id=id).first()
    template_instance.delete()
    details_fields = {
        "name": template_instance.name,
    }
    details = mergeActivityDetails(getFieldDetails(details_fields))
    addActivityLog(ActionType.TEMPLATE_DELETE, f"{template_instance.name}", details, request.user)

    return redirect('pdaAdmin:templates')

@login_required
@permission_required('pdaAdmin.templates_view', raise_exception=True)
def templates(request):
    if request.method == "POST":
        zone_template_form = ZoneTemplateForm(request.POST)
        if zone_template_form.is_valid():
            new_template = zone_template_form.save()

            details_fields = {
                "name": new_template.name,
                "kind": new_template.kind,
                "nameservers": new_template.nameservers,
            }
            details = mergeActivityDetails(getFieldDetails(details_fields))
            addActivityLog(ActionType.TEMPLATE_CREATE, f"{zone_template_form.data['name']}", details, request.user)

    else:
        zone_template_form = ZoneTemplateForm()
    zone_templates = ZoneTemplate.objects.all()
    return render(
        request,
        "web/app/admin/templates/index.html",
        {
            "active_tab": "templates",
            "page_title": _("Templates"),
            "templates": zone_templates,
            "zone_template_form":zone_template_form
        },
    )

@login_required
@permission_required('pdaAdmin.dashboard', raise_exception=True)
def edit_template(request, id):
    setting_record_types = get_setting('record_types')
    template = ZoneTemplate.objects.get(id=id)
    template_records = RecordTemplate.objects.filter(zone_template=template)
    if request.method == "POST":
        record_template_form = RecordTemplateForm(request.POST)
        zone_template_form = ZoneTemplateForm(request.POST, instance=template)

        if record_template_form.is_valid():
            record_template = record_template_form.save(commit=False)
            record_template.zone_template = template
            record_template.save()

            details_fields = {
                "template": template.name,
                "name": record_template.name,
                "type": record_template.type,
                "content": record_template.content,
                "ttl": record_template.ttl,
            }
            details = mergeActivityDetails(getFieldDetails(details_fields))
            addActivityLog(ActionType.TEMPLATE_RECORD_CREATE, f"({record_template.record_type}) {record_template.name} - {template.name} created", details, request.user)

            return redirect("pdaAdmin:edit_template", id)
        if zone_template_form.is_valid():
            new_template = zone_template_form.save()
            details_fields = {
                "old_name": template.name,
                "new_name": new_template.name,
                "old_kind": template.kind,
                "new_kind": new_template.kind,
                "old_nameservers": template.nameservers,
                "new_nameservers": new_template.nameservers,
            }
            details = mergeActivityDetails(getFieldDetails(details_fields))
            addActivityLog(ActionType.TEMPLATE_UPDATE, f"{zone_template_form.data['name']}", details, request.user)
            return redirect("pdaAdmin:edit_template", id)

    else:
        record_template_form = RecordTemplateForm()
        zone_template_form = ZoneTemplateForm(instance=template)

    return render(
        request,
        "web/app/admin/templates/edit.html",
        {
            "active_tab": "templates_create",
            "page_title": _("Zone"),
            "template":template,
            "setting_record_types":setting_record_types,
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
        addActivityLog(ActionType.CLEAR_CACHE, f"Clearing Zone and Record Cache's", "Cache Cleared", request.user)
        return redirect('pdaAdmin:dashboard')
    return redirect('pdaAdmin:dashboard')

@login_required
@permission_required('pdaAdmin.users_delete', raise_exception=True)
@require_POST
def delete_user_view(request, id):
    user_instance = CustomUser.objects.filter(id=id).first()

    if user_instance.id == 1:
        messages.add_message(request, messages.ERROR, f"Cannot Delete system user")
    elif user_instance.id == request.user.id:
        messages.add_message(request, messages.ERROR, f"Cannot Delete yourself")
    else:
        user_instance = CustomUser.objects.filter(id=id).first()
        user_instance.delete()
        details_fields = {
            "username": user_instance.username,
            "email": user_instance.email,
            "first_name": user_instance.first_name,
            "last_name": user_instance.last_name,
            "is_superuser": user_instance.is_superuser,
        }
        details = mergeActivityDetails(getFieldDetails(details_fields))
        addActivityLog(ActionType.USER_DELETE, f"{user_instance.username} ({user_instance.email})", details, request.user)
    return redirect('pdaAdmin:users')

@login_required
@permission_required('pdaAdmin.users_view', raise_exception=True)
def users(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save()  # creates and saves a new Account
            details_fields = {
                "username": new_user.username,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "is_superuser": new_user.is_superuser,
                "is_active": new_user.is_active,
            }
            details = mergeActivityDetails(getFieldDetails(details_fields))
            addActivityLog(ActionType.USER_CREATE, f"{new_user.username} ({new_user.email})", details, request.user)
    else:
        user_form = UserForm()
    users = CustomUser.objects.all()

    return render(
        request,
        "web/app/admin/users/index.html",
        {
            "active_tab": "pda_users",
            "page_title": _("Accounts"),
            "users": users,
            "user_form": user_form
        },
    )

@login_required
@permission_required('pdaAdmin.users_view', raise_exception=True)
def user(request, id):
    _user = CustomUser.objects.get(id=id)
    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == 'user':
            user_form = UserForm(request.POST, instance=_user)
            if user_form.is_valid():
                updated_user = user_form.save()  # creates and saves a new Account
                details_fields = {
                    "username": updated_user.username,
                    "email": updated_user.email,
                    "first_name": updated_user.first_name,
                    "last_name": updated_user.last_name,
                    "is_superuser": updated_user.is_superuser,
                    "is_active": updated_user.is_active,
                }
                details = mergeActivityDetails(getFieldDetails(details_fields))
                addActivityLog(ActionType.USER_CREATE, f"{updated_user.username} ({updated_user.email})", details, request.user)
                return redirect("pdaAdmin:user", id)
        if form_type == 'permissions':
            user_permission_form = UserPermissionsForm(request.POST, instance=_user)
            if user_permission_form.is_valid():
                old_perms_raw = user_permission_form.initial.get('user_permissions', [])
                old_perms = {p.id if hasattr(p, 'id') else p for p in old_perms_raw}

                new_perms_qs = user_permission_form.cleaned_data.get('user_permissions', [])
                new_perms = {p.id for p in new_perms_qs}

                updated_user = user_permission_form.save()

                permission_details = getPermissionDetails(new_perms, old_perms)
                details_fields_new = {
                    "is_superuser": updated_user.is_superuser,
                    "is_active": updated_user.is_active,
                }
                details_fields_old = {
                    "is_superuser": user_permission_form.initial.get("is_superuser"),
                    "is_active": user_permission_form.initial.get("is_active"),
                }
                field_details = getFieldDetails(details_fields_new, details_fields_old)
                details = mergeActivityDetails(field_details, permission_details)

                addActivityLog(ActionType.USER_UPDATE, f"Permissions updated for {updated_user.username}", details, request.user)
                return redirect("pdaAdmin:user", id)
        if form_type == 'groups':
            user_groups_form = UserGroupsForm(request.POST, instance=_user)
            if user_groups_form.is_valid():
                old_groups_raw = user_groups_form.initial.get('groups', [])
                old_groups = {g.id if hasattr(g, 'id') else g for g in old_groups_raw}

                new_groups_qs = user_groups_form.cleaned_data.get('groups', [])
                new_groups = {g.id for g in new_groups_qs}

                updated_user = user_groups_form.save()

                group_details = getGroupDetails(new_groups, old_groups)
                details = mergeActivityDetails(group_details)
                addActivityLog(ActionType.USER_UPDATE, f"Groups updated for {updated_user.username}", details, request.user)
                return redirect("pdaAdmin:user", id)
    else:
        user_form = UserForm(instance=_user)
        user_permission_form = UserPermissionsForm(instance=_user)
        user_groups_form = UserGroupsForm(instance=_user)

    allowed_permissions = Permission.objects.filter(
        Q(content_type__app_label='pdadns') |
        Q(content_type__app_label='pdaAdmin')
    ).exclude(
        # exclude the auto-generated crud ones from permission model
        codename__in=['add_adminpermissions', 'change_adminpermissions',
                      'delete_adminpermissions', 'view_adminpermissions',
                      'add_pdapermissions', 'change_pdapermissions', 'delete_pdapermissions', 'view_pdapermissions']
    )

    user_allowed_permissions = user_permission_form.instance.user_permissions.filter(
        Q(content_type__app_label='pdadns') |
        Q(content_type__app_label='pdaAdmin')
    ).exclude(
        codename__in=['add_adminpermissions', 'change_adminpermissions',
                      'delete_adminpermissions', 'view_adminpermissions',
                      'add_pdapermissions', 'change_pdapermissions', 'delete_pdapermissions', 'view_pdapermissions']
    )
    return render(
        request,
        "web/app/admin/users/edit.html",
        {
            "active_tab": "pda_user",
            "page_title": _("Account"),
            "user": _user,
            "user_form": user_form,
            "user_permission_form":user_permission_form,
            "user_groups_form":user_groups_form,
            "allowed_permissions":allowed_permissions,
            "user_current_permissions":user_allowed_permissions
        },
    )

@login_required
@permission_required('pdaAdmin.groups_delete', raise_exception=True)
@require_POST
def delete_group_view(request, id):
    group_instance = Group.objects.filter(id=id).first()
    group_instance.delete()
    details_fields = {
        "name": group_instance.name,
    }
    details = mergeActivityDetails(getFieldDetails(details_fields))
    addActivityLog(ActionType.GROUP_DELETE, f"{group_instance.name}", details, request.user)

    return redirect('pdaAdmin:groups')

@login_required
@permission_required('pdaAdmin.groups_view', raise_exception=True)
def groups(request):
    if request.method == "POST":
        group_form = GroupForm(request.POST)
        if group_form.is_valid():
            new_group = group_form.save()  # creates and saves a new Account
            details_fields = {
                "name": new_group.name,
            }
            details = mergeActivityDetails(getFieldDetails(details_fields))

            addActivityLog(ActionType.GROUP_CREATE, f"{group_form.data['name']}", details, request.user)
    else:
        group_form = GroupForm()
    _groups = Group.objects.all()

    return render(
        request,
        "web/app/admin/groups/index.html",
        {
            "active_tab": "pda_groups",
            "page_title": _("Accounts"),
            "groups": _groups,
            "group_form": group_form
        },
    )

@login_required
@permission_required('pdaAdmin.groups_view', raise_exception=True)
def group(request, id):
    _group = Group.objects.get(id=id)
    if request.method == "POST":
        form_type = request.POST.get('form_type')
        if form_type == 'group':
            group_form = GroupForm(request.POST, instance=_group)
            if group_form.is_valid():
                new_group = group_form.save()
                details_fields = {
                    "old_name": _group.name,
                    "new_name": new_group.name,
                }
                details = mergeActivityDetails(getFieldDetails(details_fields))
                addActivityLog(ActionType.GROUP_UPDATE, f"{_group.name}", details, request.user)
                return redirect("pdaAdmin:group", id)
        if form_type == 'permissions':
            group_permission_form = GroupPermissionsForm(request.POST, instance=_group)
            if group_permission_form.is_valid():
                old_perms_raw = group_permission_form.initial.get('permissions', [])
                old_perms = {p.id if hasattr(p, 'id') else p for p in old_perms_raw}

                new_perms_qs = group_permission_form.cleaned_data.get('permissions', [])
                new_perms = {p.id for p in new_perms_qs}

                group_permission_form.save()

                permission_details = getPermissionDetails(new_perms, old_perms)
                details = mergeActivityDetails(permission_details)

                addActivityLog(ActionType.GROUP_UPDATE, f"Permissions updated for {_group.name}", details, request.user)
                return redirect("pdaAdmin:group", id)
    else:
        group_form = GroupForm(instance=_group)
        group_permission_form = GroupPermissionsForm(instance=_group)

    allowed_permissions = Permission.objects.filter(
        Q(content_type__app_label='pdadns') |
        Q(content_type__app_label='pdaAdmin')
    ).exclude(
        codename__in=['add_adminpermissions', 'change_adminpermissions',
                      'delete_adminpermissions', 'view_adminpermissions',
                      'add_pdapermissions', 'change_pdapermissions', 'delete_pdapermissions', 'view_pdapermissions']
    )

    group_allowed_permissions = group_permission_form.instance.permissions.filter(
        Q(content_type__app_label='pdadns') |
        Q(content_type__app_label='pdaAdmin')
    ).exclude(
        codename__in=['add_adminpermissions', 'change_adminpermissions',
                      'delete_adminpermissions', 'view_adminpermissions',
                      'add_pdapermissions', 'change_pdapermissions', 'delete_pdapermissions', 'view_pdapermissions']
    )
    return render(
        request,
        "web/app/admin/groups/edit.html",
        {
            "active_tab": "pda_group",
            "page_title": _("Account"),
            "group": _group,
            "group_form": group_form,
            "group_permission_form":group_permission_form,
            "allowed_permissions": allowed_permissions,
            "group_current_permissions": group_allowed_permissions
        },
    )

def _is_valid_uuid(value):
    try:
        uuid_obj = uuid.UUID(str(value))
        return True
    except ValueError:
        return False
