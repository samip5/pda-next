"""
Django Admin configuration for PowerDNS models
"""
from django.contrib import admin
from .models import Activity



@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    readonly_fields = ['id', 'timestamp', 'action', 'user', 'details']
    list_display = ['id', 'timestamp', 'action', 'user']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['action', 'timestamp']
