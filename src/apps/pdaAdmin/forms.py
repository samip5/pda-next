from django import forms

from apps.api.accounts.models import Account
from apps.api.dns.models import Zone


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'account', 'dnssec']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'dnssec': forms.TextInput(attrs={'class': 'form-control', 'disabled': 'disabled'}),
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