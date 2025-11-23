"""
PDA Account Model

Represents account that manages zones.
"""
import uuid

from django.db import models
from apps.users.models import CustomUser as User


class Activity(models.Model):
    """
    Represents ActivityLog entry.
    """

    id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )

    action = models.CharField(
        max_length=255,
        unique=False,
        default='',
        help_text='Action taken by user or api_key'
    )

    details = models.CharField(
        max_length=255,
        unique=False,
        default='',
        help_text='Details for activity'
    )

    user = models.ForeignKey(User,
         on_delete=models.SET_NULL,
         null=True,
         blank=True,
         help_text='User who performed the action'
    )

    apikey = models.CharField(
        max_length=255,
        unique=False,
        default='',
        null=True,
        blank=True,
        help_text='Api key used'
    )

    api = models.BooleanField(
        unique=False,
        default=False,
        help_text='Log from api'
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        unique=False,
        editable=False,
        help_text='Timestamp of activity'
    )

    class Meta:
        db_table = 'pdadns_activity'
        ordering = ['id']
        verbose_name = 'ActivityLog'
        verbose_name_plural = 'ActivityLogs'
