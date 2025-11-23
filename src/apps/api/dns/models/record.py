"""
PowerDNS Record Model

Represents a DNS record within a zone.
"""
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from .zone import Zone


class Record(models.Model):
    """
    Represents a DNS record within a zone.
    
    This model stores record information for reference/tracking.
    Data is fetched on-demand from PowerDNS API.
    """
    
    RECORD_TYPE_A = 'A'
    RECORD_TYPE_AAAA = 'AAAA'
    RECORD_TYPE_CNAME = 'CNAME'
    RECORD_TYPE_MX = 'MX'
    RECORD_TYPE_TXT = 'TXT'
    RECORD_TYPE_NS = 'NS'
    RECORD_TYPE_PTR = 'PTR'
    RECORD_TYPE_SOA = 'SOA'
    RECORD_TYPE_SRV = 'SRV'
    RECORD_TYPE_CAA = 'CAA'
    
    RECORD_TYPE_CHOICES = [
        (RECORD_TYPE_A, 'A'),
        (RECORD_TYPE_AAAA, 'AAAA'),
        (RECORD_TYPE_CNAME, 'CNAME'),
        (RECORD_TYPE_MX, 'MX'),
        (RECORD_TYPE_TXT, 'TXT'),
        (RECORD_TYPE_NS, 'NS'),
        (RECORD_TYPE_PTR, 'PTR'),
        (RECORD_TYPE_SOA, 'SOA'),
        (RECORD_TYPE_SRV, 'SRV'),
        (RECORD_TYPE_CAA, 'CAA'),
    ]
    
    # Foreign key to zone
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='records',
        help_text='Zone this record belongs to'
    )
    
    # Record name (relative to zone or FQDN)
    name = models.CharField(
        max_length=255,
        help_text='Record name (relative to zone or FQDN)'
    )
    
    # Record type
    record_type = models.CharField(
        max_length=10,
        choices=RECORD_TYPE_CHOICES,
        help_text='DNS record type'
    )
    
    # Record content
    content = models.TextField(
        help_text='Record content (value)'
    )
    
    # Time to live
    ttl = models.IntegerField(
        default=3600,
        validators=[MinValueValidator(0)],
        help_text='Time to live in seconds'
    )
    
    # Whether record is disabled
    disabled = models.BooleanField(
        default=False,
        help_text='Whether this record is disabled'
    )
    
    class Meta:
        db_table = 'pdadns_records'
        ordering = ['zone', 'name', 'record_type']
        verbose_name = 'Record'
        verbose_name_plural = 'Records'
        # A zone can have multiple records with the same name and type
        # (e.g., multiple A records for load balancing)
        unique_together = [['zone', 'name', 'record_type', 'content']]
    
    def __str__(self):
        return f"{self.name} {self.record_type} {self.content}"
    
    def get_fqdn(self):
        """Get fully qualified domain name"""
        zone_name = self.zone.name.rstrip('.')
        if self.name.endswith('.'):
            return self.name
        if self.name == '@' or self.name == zone_name:
            return f"{zone_name}."
        if self.name.endswith(f".{zone_name}"):
            return f"{self.name}."
        return f"{self.name}.{zone_name}."
    
    def save(self, *args, **kwargs):
        """Override save to normalize name"""
        # Normalize name: if it's just the zone name, use '@'
        zone_name = self.zone.name.rstrip('.')
        if self.name == zone_name or self.name == f"{zone_name}.":
            self.name = '@'
        super().save(*args, **kwargs)

