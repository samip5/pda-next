"""
PDA Account Model

Represents account that manages zones.
"""
import uuid

from django.db import models
from django.core.validators import RegexValidator, EmailValidator


class Account(models.Model):
    """
    Represents account that manages zones.
    """

    id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )

    # Account name (e.g., 'cappe')
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.?$',
                message='Invalid account name format'
            )
        ],
        help_text='Account name (e.g., "cappe")'
    )

    description = models.CharField(
        max_length=255,
        unique=False,
        default='',
        help_text='Description for account'
    )

    contact = models.CharField(
        max_length=255,
        unique=False,
        default='',
        help_text='Contact for account'
    )

    mail = models.CharField(
        max_length=255,
        unique=False,
        default='',
        validators=[EmailValidator(message='Invalid email address')],
        help_text='Mail contact info for account'
    )


    class Meta:
        db_table = 'pdadns_accounts'
        ordering = ['id']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.name
