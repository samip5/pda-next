"""
Django Admin configuration for PowerDNS models
"""
from django.contrib import admin
from .models.zone import Zone
from .models.record import Record



@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    """Admin interface for Zone model"""
    list_display = ['name', 'kind', 'server_id', 'created_at']
    list_filter = ['kind', 'server_id', 'created_at']
    search_fields = ['name', 'powerdns_id']
    readonly_fields = ['powerdns_id']
    fieldsets = (
        ('Zone Information', {
            'fields': ('name', 'kind', 'nameservers', 'server_id')
        }),
        ('PowerDNS Integration', {
            'fields': ('powerdns_id',)
        }),
    )


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    """Admin interface for Record model"""
    list_display = ['name', 'record_type', 'content', 'ttl', 'zone']
    list_filter = ['record_type', 'disabled', 'zone']
    search_fields = ['name', 'content', 'zone__name']
    fieldsets = (
        ('Record Information', {
            'fields': ('zone', 'name', 'record_type', 'content', 'ttl', 'disabled')
        }),
    )
    autocomplete_fields = ['zone']

