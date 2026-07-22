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
            ("zones_soa_edit_api", "Edit zone SOA API EDIT"),
            # Zones Metadata
            ("zones_metadata_view", "View zone metadata"),
            ("zones_metadata_edit", "Edit zone metadata"),
            # Zones DNSSEC
            ("zones_dnssec_view", "View zone DNSSEC"),
            ("zones_dnssec_edit", "Edit zone DNSSEC"),

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
            ("users_permissions", "Manage user permissions"),
            ("users_groups", "Manage user groups"),
            # Groups
            ("groups_view", "View groups"),
            ("groups_create", "Create groups"),
            ("groups_delete", "Delete groups"),
            ("groups_edit", "Edit groups"),
            ("groups_permissions", "Manage group permissions"),
            # Accounts
            ("accounts_view", "View accounts"),
            ("accounts_create", "Create accounts"),
            ("accounts_delete", "Delete accounts"),
            ("accounts_edit", "Edit accounts"),
            # Templates
            ("templates_view", "View templates"),
            ("templates_create", "Create templates"),
            ("templates_delete", "Delete templates"),
            ("templates_edit", "Edit templates"),
            # Audit Log
            ("activity_log_view", "View activity log"),
            ("activity_log_details", "View more details in activity log"),
            # Cache
            ("cache_flush", "Flush cache"),
            ("settings_view", "View Settings for PDA"),
            ("settings_edit", "Edit Settings for PDA"),
            ("settings_auth", "Manage Auth settings for PDA"),
            ("settings_tsig", "Manage TSIG Keys inside settings"),
            ("dashboard", "PDA Admin Dashboard"),
        ]