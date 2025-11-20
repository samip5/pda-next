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
    readonly_fields = ['powerdns_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Zone Information', {
            'fields': ('name', 'kind', 'nameservers', 'server_id')
        }),
        ('PowerDNS Integration', {
            'fields': ('powerdns_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    """Admin interface for Record model"""
    list_display = ['name', 'record_type', 'content', 'ttl', 'zone', 'created_at']
    list_filter = ['record_type', 'disabled', 'zone', 'created_at']
    search_fields = ['name', 'content', 'zone__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Record Information', {
            'fields': ('zone', 'name', 'record_type', 'content', 'ttl', 'disabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['zone']

