from django.contrib import admin
from .models import GlobalSetting

@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'updated_at']
    list_filter = ['setting_type', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'setting_type')
        }),
        ('Additional Information', {
            'fields': ('description', 'created_at', 'updated_at')
        }),
    )
