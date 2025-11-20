from django.db import models

class ServiceType(models.Model):
    class Meta:
        permissions = (
            ("admin_settings", "Manage Settings in the admin area"),
        )
    id = models.AutoField(primary_key=True)