from django import forms

from apps.api.accounts.models import Account
from apps.api.dns.models import Zone
from apps.api.templates.models import ZoneTemplate, RecordTemplate


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
            'members': forms.CheckboxSelectMultiple(),
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