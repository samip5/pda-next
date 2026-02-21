from django.db import models

class AdminPermissions(models.Model):
    class Meta:
        managed = False
        verbose_name = "PDA Admin"
        verbose_name_plural = "PDA Admin"
        permissions = [
            # Zones
            ("zones_view", "View zones"),
            ("zones_create", "Create zones"),
            ("zones_delete", "Delete zones"),
            ("zones_edit", "Edit zones"),
            # Records
            ("records_view", "View records"),
            ("records_create", "Create records"),
            ("records_delete", "Delete records"),
            ("records_edit", "Edit records"),
            # Users
            ("users_view", "View users"),
            ("users_create", "Create users"),
            ("users_delete", "Delete users"),
            ("users_edit", "Edit users"),
            # Groups
            ("groups_view", "View groups"),
            ("groups_create", "Create groups"),
            ("groups_delete", "Delete groups"),
            ("groups_edit", "Edit groups"),
            # Accounts
            ("accounts_view", "View accounts"),
            ("accounts_create", "Create accounts"),
            ("accounts_delete", "Delete accounts"),
            ("accounts_edit", "Edit accounts"),
            # Audit Log
            ("activity_log_view", "View activity log"),
            ("activity_log_details", "View more details in activity log"),
            # Cache
            ("cache_flush", "Flush cache"),
        ]