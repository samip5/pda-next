"""
PDA Account Model

Represents account that manages zones.
"""
import uuid

from django.db import models
from apps.users.models import CustomUser as User


class ActionType(models.TextChoices):
    ZONE_CREATE = 'zone_create', 'Zone Create'
    ZONE_UPDATE = 'zone_update', 'Zone Update'
    ZONE_DELETE = 'zone_delete', 'Zone Delete'
    RECORD_CREATE = 'record_create', 'Record Create'
    RECORD_UPDATE = 'record_update', 'Record Update'
    RECORD_DELETE = 'record_delete', 'Record Delete'
    ACCOUNT_CREATE = 'account_create', 'Account Create'
    ACCOUNT_UPDATE = 'account_update', 'Account Update'
    ACCOUNT_DELETE = 'account_delete', 'Account Delete'
    TEMPLATE_CREATE = 'template_create', 'Template Create'
    TEMPLATE_UPDATE = 'template_update', 'Template Update'
    TEMPLATE_DELETE = 'template_delete', 'Template Delete'
    TEMPLATE_RECORD_CREATE = 'template_record_create', 'Template Record Create'
    TEMPLATE_RECORD_UPDATE = 'template_record_update', 'Template Record Update'
    TEMPLATE_RECORD_DELETE = 'template_record_delete', 'Template Record Delete'
    USER_CREATE = 'user_create', 'User Create'
    USER_UPDATE = 'user_update', 'User Update'
    USER_DELETE = 'user_delete', 'User Delete'
    USER_LOGIN = 'user_login', 'User Login'
    USER_SIGNUP = 'user_signup', 'User Signup'
    USER_APIKEY_CREATE = 'user_apikey_create', 'User APIKey Create'
    USER_APIKEY_UPDATE = 'user_apikey_update', 'User APIKey Update'
    USER_APIKEY_DELETE = 'user_apikey_delete', 'User APIKey Delete'
    APP_SETTING_CHANGE = 'app_setting_change', 'App Setting Change'


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
        choices=ActionType.choices,
        help_text='Action taken'
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
