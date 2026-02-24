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
            ("users_manage", "Manage users"),
            ("users_permissions", "Manage user permissions"),
            ("users_groups", "Manage user groups"),
            # Groups
            ("groups_view", "View groups"),
            ("groups_manage", "Manage groups"),
            ("groups_permissions", "Manage group permissions"),
            # Accounts
            ("accounts_view", "View accounts"),
            ("accounts_manage", "Manage accounts"),
            # Templates
            ("templates_view", "View templates"),
            ("templates_manage", "Manage templates"),
            # Audit Log
            ("activity_log_view", "View activity log"),
            ("activity_log_details", "View more details in activity log"),
            # Cache
            ("cache_flush", "Flush cache"),
            ("settings", "Settings for PDA"),
            ("dashboard", "PDA Admin Dashboard"),
        ]