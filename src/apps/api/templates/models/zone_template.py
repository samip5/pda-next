"""
PDA Zone Template Model

Represents a zone but in a template form.
"""
import uuid

from django.db import models
from django.core.validators import RegexValidator, EmailValidator


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

    user = models.CharField(
        max_length=255,
        unique=False,
        default='',
        blank=True,
        help_text='User id'
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

    def __str__(self):
        return self.name
