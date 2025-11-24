from django.db import models
from django.core.cache import cache

class GlobalSetting(models.Model):
    """
    Model for storing global application settings in the database.
    """
    SETTING_TYPES = (
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('float', 'Float'),
        ('json', 'JSON'),
    )

    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Description of this setting")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'global_settings'
        verbose_name = "Global Setting"
        verbose_name_plural = "Global Settings"
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    def get_value(self):
        """Convert the stored value to its appropriate type"""
        import json

        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value

    def save(self, *args, **kwargs):
        """Clear cache when saving"""
        super().save(*args, **kwargs)
        cache.delete(f'global_setting_{self.key}')
        cache.delete('all_global_settings')