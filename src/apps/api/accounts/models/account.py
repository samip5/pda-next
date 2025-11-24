"""
PDA Account Model

Represents account that manages zones.
"""
import uuid

from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from apps.users.models import CustomUser as User


class Account(models.Model):
    """
    Represents account that manages zones.
    """

    id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Account name'
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

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        related_name='account_owner',
        default=None,
        null=True,
        blank=True,
        help_text='Account owner'
    )
    members = models.ManyToManyField(
        User,
        default=None,
        null=True,
        blank=True,
        help_text='Account Members'
    )

    class Meta:
        db_table = 'pda_accounts'
        ordering = ['id']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.name



class AccountMembership(models.Model):
    """Links users to accounts with roles"""

    class Meta:
        db_table = "pda_account_memberships"
        unique_together = ('user', 'account')

    class Role(models.TextChoices):
        """
         OWNER = Zone belongs to that user
         ADMIN = Application administrator
         MEMBER = Regular member
        """
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_memberships')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user} - {self.account} ({self.role})"
