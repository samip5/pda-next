from django.db import models

class PDAPermissions(models.Model):
    class Meta:
        managed = False
        verbose_name = "PDA"
        verbose_name_plural = "PDA"
        permissions = [
            # Zones
            ("zones_view", "View zones"),
        ]