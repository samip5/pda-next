"""
PowerDNS Zone Model

Represents a DNS zone in PowerDNS.
"""
import uuid

from django.db import models
from django.core.validators import RegexValidator


class ZoneTemplate(models.Model):
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

    id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    name = models.CharField(
        max_length=255,
        default=None,
        help_text='Zone template name'
    )

    account = models.UUIDField(
        max_length=255,
        unique=False,
        default=None,
        null=True,
        blank=True,
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

    class Meta:
        db_table = 'pdadns_templates_zones'
        ordering = ['id']
        verbose_name = 'Zone template'
        verbose_name_plural = 'Zone templates'

    def __str__(self):
        return self.id

