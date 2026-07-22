from django.db import models

class PDAPermissions(models.Model):
    class Meta:
        managed = False
        verbose_name = "PDA"
        verbose_name_plural = "PDA"
        permissions = [
            ("api_keys", "Allow's user to create and revoke their own API keys"),

            ('zones_view', 'View owned zones'),
            ('zones_dnssec_view', 'View DNSSEC of owned zones'),
            ('zones_dnssec_edit', 'Manage DNSSEC of owned zones'),

            ('records_view', 'View records of owned zones'),
            ('records_create', 'Create records on owned zones'),
            ('records_delete', 'Delete records of owned zones'),
            ('records_edit', 'Edit records of owned zones')
        ]