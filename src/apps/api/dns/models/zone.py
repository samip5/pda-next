"""
PowerDNS Zone Model

Represents a DNS zone in PowerDNS.
"""
from django.db import models
from django.core.validators import RegexValidator
from apps.api.accounts.models import Account
from apps.users.models import CustomUser as User

class Zone(models.Model):
    """
    Represents a DNS zone managed by PowerDNS.
    
    This model stores zone information for reference/tracking.
    Data is fetched on-demand from PowerDNS API.
    """
    
    ZONE_KIND_NATIVE = 'Native'
    ZONE_KIND_MASTER = 'Master'
    ZONE_KIND_SLAVE = 'Slave'
    
    ZONE_KIND_CHOICES = [
        (ZONE_KIND_NATIVE, 'Native'),
        (ZONE_KIND_MASTER, 'Master'),
        (ZONE_KIND_SLAVE, 'Slave'),
    ]
    
    # Zone name (e.g., 'example.com.')
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.?$',
                message='Invalid zone name format'
            )
        ],
        help_text='Zone name (e.g., example.com.)'
    )

    # Zone account
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='zones',
        null=True,
        blank=True,
        help_text='Associated account for the zone'
    )

    # Zone dnssec status
    dnssec = models.BooleanField(
        max_length=255,
        unique=False,
        default=False,
        help_text='Zone DNSSEC status'
    )

    # Zone kind
    kind = models.CharField(
        max_length=20,
        choices=ZONE_KIND_CHOICES,
        default=ZONE_KIND_NATIVE,
        help_text='Zone kind (Native, Master, or Slave)'
    )
    
    # Nameservers
    nameservers = models.JSONField(
        default=list,
        help_text='List of nameserver hostnames'
    )
    
    # PowerDNS server ID
    server_id = models.CharField(
        max_length=100,
        default='localhost',
        help_text='PowerDNS server ID'
    )
    
    # PowerDNS zone ID (from API, cached for reference)
    powerdns_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='PowerDNS zone ID (cached from API)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_zones')
    soa_serial = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        validators=(MinValueValidator(0), MaxValueValidator(4294967295)),
        editable=False,
        help_text='SOA serial number'
    )

    class Meta:
        db_table = 'pdadns_zones'
        ordering = ['name']
        verbose_name = 'Zone'
        verbose_name_plural = 'Zones'
        permissions = [
            ("manage_zone_dnssec", "Can enable or disable DNSSEC for the zone"),
            ("manage_zone_records", "Can create, update, or delete records in the zone"),
            ("sync_zone", "Can sync zone data from PowerDNS"),
        ]

    def __str__(self):
        return self.name

    def ensure_trailing_dot(self):
        if not self.name.endswith('.'):
            self.name = f"{self.name}."

    def save(self, *args, **kwargs):
        self.ensure_trailing_dot()
        super().save(*args, **kwargs)
