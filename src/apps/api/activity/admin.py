"""
Django Admin configuration for PowerDNS models
"""
from django.contrib import admin
from .models import Activity



@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    readonly_fields = ['id', 'timestamp', 'action', 'user', 'details', 'api', 'apikey']
    list_display = ['details', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['action', 'timestamp']
