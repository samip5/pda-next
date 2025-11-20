"""
Tests for PowerDNS API Client
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
import requests

from apps.pdadns.client import (
    PowerDNSClient,
    PowerDNSError,
    PowerDNSConnectionError,
    PowerDNSUnauthorizedError,
    PowerDNSNotFoundError,
)


class PowerDNSClientTestCase(TestCase):
    """Test cases for PowerDNSClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_url = 'http://localhost:8081/api/v1'
        self.api_key = 'test-api-key'
        self.client = PowerDNSClient(
            api_url=self.api_url,
            api_key=self.api_key,
            timeout=30
        )
    
    def test_init_with_config(self):
        """Test client initialization with config values"""
        with patch('apps.pdadns.client.app_settings') as mock_settings:
            mock_settings.powerdns_api_url = 'http://test:8081/api/v1'
            mock_settings.powerdns_api_key = 'config-key'
            mock_settings.powerdns_api_timeout = 60
            
            client = PowerDNSClient()
            self.assertEqual(client.api_url, 'http://test:8081/api/v1/')
            self.assertEqual(client.api_key, 'config-key')
            self.assertEqual(client.timeout, 60)
    
    def test_init_missing_url(self):
        """Test client initialization fails without API URL"""
        with patch('apps.pdadns.client.app_settings') as mock_settings:
            mock_settings.powerdns_api_url = ''
            mock_settings.powerdns_api_key = 'key'
            
            with self.assertRaises(ValueError):
                PowerDNSClient()
    
    def test_init_missing_key(self):
        """Test client initialization fails without API key"""
        with patch('apps.pdadns.client.app_settings') as mock_settings:
            mock_settings.powerdns_api_url = 'http://test/api/v1'
            mock_settings.powerdns_api_key = ''
            
            with self.assertRaises(ValueError):
                PowerDNSClient()
    
    def test_init_url_trailing_slash(self):
        """Test that API URL gets trailing slash added"""
        client = PowerDNSClient(api_url='http://test/api/v1', api_key='key')
        self.assertEqual(client.api_url, 'http://test/api/v1/')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_get_servers(self, mock_session_class):
        """Test getting list of servers"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 'localhost', 'type': 'Server'}]
        mock_response.content = b'{}'
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        result = client.get_servers()
        
        self.assertEqual(result, [{'id': 'localhost', 'type': 'Server'}])
        mock_session.request.assert_called_once()
    
    @patch('apps.pdadns.client.requests.Session')
    def test_get_zone(self, mock_session_class):
        """Test getting a zone"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'kind': 'Native'
        }
        mock_response.content = b'{}'
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        result = client.get_zone('example.com.')
        
        self.assertEqual(result['name'], 'example.com.')
        self.assertEqual(result['kind'], 'Native')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_get_zone_not_found(self, mock_session_class):
        """Test getting a non-existent zone"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Zone not found'
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        
        with self.assertRaises(PowerDNSNotFoundError):
            client.get_zone('nonexistent.com.')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_get_zone_unauthorized(self, mock_session_class):
        """Test getting a zone with invalid API key"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key='invalid-key')
        
        with self.assertRaises(PowerDNSUnauthorizedError):
            client.get_zone('example.com.')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_create_zone(self, mock_session_class):
        """Test creating a zone"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'kind': 'Native',
            'nameservers': ['ns1.example.com.']
        }
        mock_response.content = b'{}'
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        result = client.create_zone(
            zone_name='example.com.',
            nameservers=['ns1.example.com.']
        )
        
        self.assertEqual(result['name'], 'example.com.')
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        self.assertEqual(call_args[1]['method'], 'POST')
        self.assertIn('nameservers', call_args[1]['json'])
    
    @patch('apps.pdadns.client.requests.Session')
    def test_create_record(self, mock_session_class):
        """Test creating a DNS record"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock get_zone response
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'id': 'example.com.',
            'name': 'example.com.',
            'rrsets': []
        }
        mock_get_response.content = b'{}'
        
        # Mock patch response
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 204
        mock_patch_response.content = b''
        
        mock_session.request.side_effect = [mock_get_response, mock_patch_response]
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        result = client.create_record(
            zone_name='example.com.',
            name='www',
            record_type='A',
            content='192.0.2.1'
        )
        
        # Should have called GET (get_zone) and PATCH (create_record)
        self.assertEqual(mock_session.request.call_count, 2)
    
    @patch('apps.pdadns.client.requests.Session')
    def test_delete_zone(self, mock_session_class):
        """Test deleting a zone"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_session.request.return_value = mock_response
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        client.delete_zone('example.com.')
        
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        self.assertEqual(call_args[1]['method'], 'DELETE')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_connection_error(self, mock_session_class):
        """Test handling connection errors"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.exceptions.ConnectionError('Connection failed')
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        
        with self.assertRaises(PowerDNSConnectionError):
            client.get_zone('example.com.')
    
    @patch('apps.pdadns.client.requests.Session')
    def test_timeout_error(self, mock_session_class):
        """Test handling timeout errors"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.exceptions.Timeout('Request timed out')
        
        client = PowerDNSClient(api_url=self.api_url, api_key=self.api_key)
        
        with self.assertRaises(PowerDNSConnectionError):
            client.get_zone('example.com.')

