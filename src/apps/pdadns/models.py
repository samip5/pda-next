from django.db import models

class PDAPermissions(models.Model):
    class Meta:
        managed = False
        verbose_name = "PDA"
        verbose_name_plural = "PDA"
        permissions = [
            ("api_keys", "Allow's user to create and revoke their own API keys"),
        ]