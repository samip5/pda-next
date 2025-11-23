"""
Django Admin configuration for PowerDNS models
"""
from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for Record model"""
    list_display = ['id','name', 'contact']

