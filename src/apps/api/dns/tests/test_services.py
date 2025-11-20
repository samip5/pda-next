"""
Tests for PowerDNS Service Layer
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.pdadns.client import PowerDNSClient, PowerDNSNotFoundError
from apps.pdadns.services import PowerDNSService


class PowerDNSServiceTestCase(TestCase):
    """Test cases for PowerDNSService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=PowerDNSClient)
        self.service = PowerDNSService(client=self.mock_client)
    
    def test_get_zones(self):
        """Test fetching all zones from PowerDNS"""
        self.mock_client.get_zones.return_value = [
            {'id': 'example.com.', 'name': 'example.com.', 'kind': 'Native'},
            {'id': 'test.com.', 'name': 'test.com.', 'kind': 'Master'}
        ]
        
        zones = self.service.get_zones()
        
        self.assertEqual(len(zones), 2)
        self.assertEqual(zones[0]['name'], 'example.com.')
        self.mock_client.get_zones.assert_called_once_with('localhost')
    
    def test_get_zone(self):
        """Test fetching a specific zone from PowerDNS"""
        self.mock_client.get_zone.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'kind': 'Native',
            'nameservers': ['ns1.example.com.']
        }
        
        zone = self.service.get_zone('example.com.')
        
        self.assertIsNotNone(zone)
        self.assertEqual(zone['name'], 'example.com.')
        self.assertEqual(zone['kind'], 'Native')
        self.mock_client.get_zone.assert_called_once_with('example.com.', 'localhost')
    
    def test_get_zone_not_found(self):
        """Test fetching a non-existent zone"""
        self.mock_client.get_zone.side_effect = PowerDNSNotFoundError('Zone not found')
        
        zone = self.service.get_zone('nonexistent.com.')
        
        self.assertIsNone(zone)
    
    def test_get_records(self):
        """Test fetching records for a zone"""
        self.mock_client.get_records.return_value = [
            {
                'name': 'www.example.com.',
                'type': 'A',
                'ttl': 3600,
                'records': [{'content': '192.0.2.1', 'disabled': False}]
            },
            {
                'name': 'example.com.',
                'type': 'MX',
                'ttl': 3600,
                'records': [{'content': '10 mail.example.com.', 'disabled': False}]
            }
        ]
        
        records = self.service.get_records('example.com.')
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['type'], 'A')
        self.mock_client.get_records.assert_called_once_with('example.com.', 'localhost')
    
    def test_create_zone(self):
        """Test creating a zone in PowerDNS"""
        self.mock_client.create_zone.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'kind': 'Native',
            'nameservers': ['ns1.example.com.']
        }
        
        result = self.service.create_zone(
            zone_name='example.com.',
            nameservers=['ns1.example.com.'],
            kind='Native'
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'example.com.')
        self.mock_client.create_zone.assert_called_once()
    
    def test_update_zone(self):
        """Test updating a zone in PowerDNS"""
        self.mock_client.update_zone.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'kind': 'Master',
            'nameservers': ['ns1.example.com.', 'ns2.example.com.']
        }
        
        result = self.service.update_zone(
            zone_name='example.com.',
            kind='Master',
            nameservers=['ns1.example.com.', 'ns2.example.com.']
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['kind'], 'Master')
        self.mock_client.update_zone.assert_called_once()
    
    def test_delete_zone(self):
        """Test deleting a zone from PowerDNS"""
        self.mock_client.delete_zone.return_value = None
        
        result = self.service.delete_zone('example.com.')
        
        self.assertTrue(result)
        self.mock_client.delete_zone.assert_called_once_with('example.com.', 'localhost')
    
    def test_create_record(self):
        """Test creating a record in PowerDNS"""
        # Mock get_zone for create_record
        self.mock_client.get_zone.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'rrsets': []
        }
        self.mock_client.create_record.return_value = {}
        
        result = self.service.create_record(
            zone_name='example.com.',
            name='www',
            record_type='A',
            content='192.0.2.1'
        )
        
        self.assertIsNotNone(result)
        self.mock_client.create_record.assert_called_once()
    
    def test_update_record(self):
        """Test updating a record in PowerDNS"""
        # Mock get_zone for update_record
        self.mock_client.get_zone.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'rrsets': [
                {
                    'name': 'www.example.com.',
                    'type': 'A',
                    'ttl': 3600,
                    'records': [{'content': '192.0.2.1', 'disabled': False}]
                }
            ]
        }
        self.mock_client.update_record.return_value = {}
        
        result = self.service.update_record(
            zone_name='example.com.',
            name='www',
            record_type='A',
            old_content='192.0.2.1',
            new_content='192.0.2.2'
        )
        
        self.assertIsNotNone(result)
        self.mock_client.update_record.assert_called_once()
    
    def test_delete_record(self):
        """Test deleting a record from PowerDNS"""
        self.mock_client.delete_record.return_value = {}
        
        result = self.service.delete_record(
            zone_name='example.com.',
            name='www',
            record_type='A',
            content='192.0.2.1'
        )
        
        self.assertIsNotNone(result)
        self.mock_client.delete_record.assert_called_once()

