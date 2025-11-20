"""
Tests for PowerDNS Models
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.pdadns.models.zone import Zone
from apps.pdadns.models.record import Record


class ZoneModelTestCase(TestCase):
    """Test cases for Zone model"""
    
    def test_zone_creation(self):
        """Test creating a zone"""
        zone = Zone.objects.create(
            name='example.com.',
            kind=Zone.ZONE_KIND_NATIVE,
            nameservers=['ns1.example.com.', 'ns2.example.com.']
        )
        
        self.assertEqual(zone.name, 'example.com.')
        self.assertEqual(zone.kind, Zone.ZONE_KIND_NATIVE)
        self.assertEqual(len(zone.nameservers), 2)
    
    def test_zone_ensure_trailing_dot(self):
        """Test that zone name gets trailing dot"""
        zone = Zone(name='example.com')
        zone.ensure_trailing_dot()
        self.assertEqual(zone.name, 'example.com.')
        
        zone = Zone(name='example.com.')
        zone.ensure_trailing_dot()
        self.assertEqual(zone.name, 'example.com.')
    
    def test_zone_save_adds_trailing_dot(self):
        """Test that save() automatically adds trailing dot"""
        zone = Zone.objects.create(
            name='example.com',
            kind=Zone.ZONE_KIND_NATIVE,
            nameservers=[]
        )
        
        # Reload from database
        zone.refresh_from_db()
        self.assertEqual(zone.name, 'example.com.')
    
    def test_zone_str(self):
        """Test zone string representation"""
        zone = Zone.objects.create(
            name='example.com.',
            kind=Zone.ZONE_KIND_NATIVE,
            nameservers=[]
        )
        self.assertEqual(str(zone), 'example.com.')
    
    def test_zone_unique_name(self):
        """Test that zone names must be unique"""
        Zone.objects.create(
            name='example.com.',
            kind=Zone.ZONE_KIND_NATIVE,
            nameservers=[]
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Zone.objects.create(
                name='example.com.',
                kind=Zone.ZONE_KIND_NATIVE,
                nameservers=[]
            )


class RecordModelTestCase(TestCase):
    """Test cases for Record model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.zone = Zone.objects.create(
            name='example.com.',
            kind=Zone.ZONE_KIND_NATIVE,
            nameservers=['ns1.example.com.']
        )
    
    def test_record_creation(self):
        """Test creating a record"""
        record = Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1',
            ttl=3600
        )
        
        self.assertEqual(record.zone, self.zone)
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.record_type, Record.RECORD_TYPE_A)
        self.assertEqual(record.content, '192.0.2.1')
        self.assertEqual(record.ttl, 3600)
        self.assertFalse(record.disabled)
    
    def test_record_get_fqdn(self):
        """Test getting FQDN for a record"""
        record = Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        fqdn = record.get_fqdn()
        self.assertEqual(fqdn, 'www.example.com.')
    
    def test_record_get_fqdn_at_symbol(self):
        """Test FQDN for @ (zone root) record"""
        record = Record.objects.create(
            zone=self.zone,
            name='@',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        fqdn = record.get_fqdn()
        self.assertEqual(fqdn, 'example.com.')
    
    def test_record_get_fqdn_fqdn_input(self):
        """Test FQDN when record name is already FQDN"""
        record = Record.objects.create(
            zone=self.zone,
            name='subdomain.example.com.',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        fqdn = record.get_fqdn()
        self.assertEqual(fqdn, 'subdomain.example.com.')
    
    def test_record_save_normalizes_zone_name(self):
        """Test that save() normalizes zone name to @"""
        record = Record.objects.create(
            zone=self.zone,
            name='example.com',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        # Reload from database
        record.refresh_from_db()
        self.assertEqual(record.name, '@')
    
    def test_record_str(self):
        """Test record string representation"""
        record = Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        expected = 'www A 192.0.2.1'
        self.assertEqual(str(record), expected)
    
    def test_record_unique_together(self):
        """Test that same record can't be created twice"""
        Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        # Same record should raise IntegrityError
        with self.assertRaises(Exception):  # IntegrityError
            Record.objects.create(
                zone=self.zone,
                name='www',
                record_type=Record.RECORD_TYPE_A,
                content='192.0.2.1'
            )
    
    def test_record_multiple_same_type(self):
        """Test that multiple records of same type can exist with different content"""
        Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        # Different content should be allowed
        record2 = Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.2'
        )
        
        self.assertIsNotNone(record2)
        self.assertEqual(record2.content, '192.0.2.2')
    
    def test_record_zone_cascade_delete(self):
        """Test that deleting zone deletes records"""
        Record.objects.create(
            zone=self.zone,
            name='www',
            record_type=Record.RECORD_TYPE_A,
            content='192.0.2.1'
        )
        
        self.assertEqual(Record.objects.count(), 1)
        
        self.zone.delete()
        
        self.assertEqual(Record.objects.count(), 0)

