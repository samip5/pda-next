import json

from allauth.socialaccount.models import SocialApp
from django import forms
from django.contrib.auth.models import Permission, Group

from apps.api.accounts.models import Account
from apps.api.dns.models import Zone
from apps.api.templates.models import ZoneTemplate, RecordTemplate
from apps.users.models import CustomUser


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'account', 'dnssec']
        widgets = {
            'name': forms.TextInput(),
            'account': forms.Select(),
            'dnssec': forms.TextInput(attrs={'disabled': 'disabled'}),
        }

class CreateZoneForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=ZoneTemplate.objects.all(),
        required=False,               # optional if you want
        label="Template",
        empty_label="Select a template",
        widget=forms.Select()
    )
    class Meta:
        model = Zone
        fields = ['name', 'account', 'dnssec', 'template']
        widgets = {
            'name': forms.TextInput(),
            'account': forms.Select(),
            'dnssec': forms.TextInput(attrs={'disabled': 'disabled'}),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'mail', 'contact', 'description', 'owner', 'members']
        widgets = {
            'name': forms.TextInput(),
            'mail': forms.EmailInput(),
            'contact': forms.TextInput(),
            'description': forms.Textarea(),
            'owner': forms.Select(),
            'members': forms.SelectMultiple(attrs={'id': 'id_members', 'hidden': True}),
        }


class ZoneTemplateForm(forms.ModelForm):
    class Meta:
        model = ZoneTemplate
        fields = ['name', 'kind', 'nameservers']
        widgets = {
            'name': forms.TextInput(),
            'kind': forms.Select(),
            'nameservers': forms.TextInput,
        }

class RecordTemplateForm(forms.ModelForm):
    class Meta:
        model = RecordTemplate
        fields = ['name', 'record_type', 'content', 'ttl']
        widgets = {
            'name': forms.TextInput(),
            'record_type': forms.Select(),
            'content': forms.Textarea(),
            'ttl': forms.NumberInput(),
        }

class DeleteZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields= ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active']
        widgets = {
            'username': forms.TextInput(),
            'email': forms.EmailInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'is_superuser': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
        }

class UserPermissionsForm(forms.ModelForm):
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'id': 'all-permissions', 'size': 10}),
        label="Permissions"
    )

    class Meta:
        model = CustomUser
        fields = ['user_permissions']

class UserGroupsForm(forms.ModelForm):
    user_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'id': 'all-permissions', 'size': 10}),
        label="Groups"
    )

    class Meta:
        model = CustomUser
        fields = ['groups']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }

class GroupPermissionsForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'id': 'all-permissions', 'size': 10}),
        label="Permissions"
    )
    class Meta:
        model = Group
        fields = ['permissions']


class SocialAppForm(forms.ModelForm):
    class Meta:
        model = SocialApp
        fields = ['provider','provider_id', 'name', 'client_id', 'secret', 'key', 'sites', 'settings']
        widgets = {
            'name': forms.TextInput(),
            'secret': forms.PasswordInput(render_value=True),
            'key': forms.PasswordInput(render_value=True),
            'sites': forms.CheckboxSelectMultiple(),
            'settings': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"server_url":""}'}),
        }

        def clean_settings(self):
            data = self.cleaned_data.get('settings')
            if not data:
                return {}
            try:
                # If it's already a dict (from initial data), leave it.
                # If it's a string (from form input), parse it.
                if isinstance(data, str):
                    return json.loads(data)
                return data
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format.")