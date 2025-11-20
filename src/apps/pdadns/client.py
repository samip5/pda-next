"""
PowerDNS API Client

This module provides a client for interacting with the PowerDNS API.
It handles authentication, requests, and error handling.
"""
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin

import requests
from django.conf import settings
from config import settings as app_settings

logger = logging.getLogger("pdadns")


class PowerDNSError(Exception):
    """Base exception for PowerDNS API errors"""
    pass


class PowerDNSConnectionError(PowerDNSError):
    """Raised when connection to PowerDNS API fails"""
    pass


class PowerDNSUnauthorizedError(PowerDNSError):
    """Raised when authentication fails"""
    pass


class PowerDNSNotFoundError(PowerDNSError):
    """Raised when a resource is not found"""
    pass


class PowerDNSClient:
    """
    Client for interacting with PowerDNS API.
    
    Handles authentication via API key and provides methods for
    managing zones and records.
    """
    
    def __init__(self):
        """
        Initialize PowerDNS client.
        
        Args:
            api_url: PowerDNS API URL (defaults to config setting)
            api_key: PowerDNS API key (defaults to config setting)
            timeout: Request timeout in seconds (defaults to config setting)
        """
        self.api_url = app_settings.powerdns_api_url
        self.api_key = app_settings.powerdns_api_key
        self.timeout = app_settings.powerdns_api_timeout
        
        if not self.api_url:
            raise ValueError("PowerDNS API URL is required")
        if not self.api_key:
            raise ValueError("PowerDNS API key is required")
        
        # Ensure API URL ends with /
        if not self.api_url.endswith('/'):
            self.api_url += '/'
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the PowerDNS API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (relative to base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Response JSON data
            
        Raises:
            PowerDNSConnectionError: On connection errors
            PowerDNSUnauthorizedError: On authentication errors
            PowerDNSNotFoundError: On 404 errors
            PowerDNSError: On other API errors
        """
        url = urljoin(self.api_url, endpoint.lstrip('/'))
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Handle errors
            if response.status_code == 401:
                raise PowerDNSUnauthorizedError(
                    f"PowerDNS API authentication failed: {response.text}"
                )
            elif response.status_code == 404:
                raise PowerDNSNotFoundError(
                    f"Resource not found: {endpoint}"
                )
            elif response.status_code >= 400:
                error_msg = response.text or f"HTTP {response.status_code}"
                raise PowerDNSError(
                    f"PowerDNS API error ({response.status_code}): {error_msg}"
                )
            
            # Return JSON if available, otherwise empty dict
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.Timeout:
            raise PowerDNSConnectionError(
                f"PowerDNS API request timed out after {self.timeout}s"
            )
        except requests.exceptions.ConnectionError as e:
            raise PowerDNSConnectionError(
                f"Failed to connect to PowerDNS API at {self.api_url}: {e}"
            )
        except requests.exceptions.RequestException as e:
            raise PowerDNSConnectionError(
                f"PowerDNS API request failed: {e}"
            )
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of PowerDNS servers"""
        return self._request('GET', 'servers')
    
    def get_server(self, server_id: str = 'localhost') -> Dict[str, Any]:
        """Get server information"""
        return self._request('GET', f'servers/{server_id}')
    
    def get_zones(self, server_id: str = 'localhost') -> List[Dict[str, Any]]:
        """Get list of zones"""
        return self._request('GET', f'servers/{server_id}/zones')
    
    def get_zone(self, zone_name: str, server_id: str = 'localhost') -> Dict[str, Any]:
        """
        Get zone information.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Zone information dictionary
        """
        return self._request('GET', f'servers/{server_id}/zones/{zone_name}')
    
    def create_zone(
        self,
        zone_name: str,
        nameservers: List[str],
        kind: str = 'Native',
        server_id: str = 'localhost',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new zone.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            nameservers: List of nameserver hostnames
            kind: Zone kind (Native, Master, Slave)
            server_id: Server ID (default: 'localhost')
            **kwargs: Additional zone parameters
            
        Returns:
            Created zone information
        """
        zone_data = {
            'name': zone_name,
            'kind': kind,
            'nameservers': nameservers,
            **kwargs
        }
        return self._request('POST', f'servers/{server_id}/zones', data=zone_data)
    
    def update_zone(
        self,
        zone_name: str,
        server_id: str = 'localhost',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update zone information.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            **kwargs: Zone parameters to update
            
        Returns:
            Updated zone information
        """
        return self._request(
            'PUT',
            f'servers/{server_id}/zones/{zone_name}',
            data=kwargs
        )
    
    def delete_zone(
        self,
        zone_name: str,
        server_id: str = 'localhost'
    ) -> None:
        """
        Delete a zone.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
        """
        self._request('DELETE', f'servers/{server_id}/zones/{zone_name}')
    
    def get_records(
        self,
        zone_name: str,
        server_id: str = 'localhost'
    ) -> List[Dict[str, Any]]:
        """
        Get all records in a zone.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            
        Returns:
            List of record dictionaries
        """
        zone = self.get_zone(zone_name, server_id)
        return zone.get('rrsets', [])
    
    def create_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        content: str,
        ttl: int = 3600,
        server_id: str = 'localhost'
    ) -> Dict[str, Any]:
        """
        Create a new DNS record.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            content: Record content
            ttl: Time to live in seconds
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone information
        """
        # Ensure name ends with zone name or is FQDN
        if not name.endswith('.'):
            if not name.endswith(zone_name.rstrip('.')):
                name = f"{name}.{zone_name}".rstrip('.')
            name = f"{name}."
        
        # Get existing records for the zone
        zone = self.get_zone(zone_name, server_id)
        rrsets = zone.get('rrsets', [])
        
        # Find existing rrset for this name and type
        existing_rrset = None
        for rrset in rrsets:
            if rrset.get('name') == name and rrset.get('type') == record_type:
                existing_rrset = rrset
                break
        
        if existing_rrset:
            # Add to existing rrset
            records = existing_rrset.get('records', [])
            records.append({'content': content, 'disabled': False})
            rrset_data = {
                'rrsets': [{
                    'name': name,
                    'type': record_type,
                    'ttl': ttl,
                    'changetype': 'REPLACE',
                    'records': records
                }]
            }
        else:
            # Create new rrset
            rrset_data = {
                'rrsets': [{
                    'name': name,
                    'type': record_type,
                    'ttl': ttl,
                    'changetype': 'REPLACE',
                    'records': [{'content': content, 'disabled': False}]
                }]
            }
        
        return self._request(
            'PATCH',
            f'servers/{server_id}/zones/{zone_name}',
            data=rrset_data
        )
    
    def update_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        old_content: str,
        new_content: str,
        ttl: Optional[int] = None,
        server_id: str = 'localhost'
    ) -> Dict[str, Any]:
        """
        Update an existing DNS record.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            old_content: Current record content
            new_content: New record content
            ttl: Time to live in seconds (optional)
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone information
        """
        # Ensure name ends with zone name or is FQDN
        if not name.endswith('.'):
            if not name.endswith(zone_name.rstrip('.')):
                name = f"{name}.{zone_name}".rstrip('.')
            name = f"{name}."
        
        # Get existing records
        zone = self.get_zone(zone_name, server_id)
        rrsets = zone.get('rrsets', [])
        
        # Find and update the record
        for rrset in rrsets:
            if rrset.get('name') == name and rrset.get('type') == record_type:
                records = rrset.get('records', [])
                updated_records = []
                found = False
                
                for record in records:
                    if record.get('content') == old_content:
                        updated_records.append({
                            'content': new_content,
                            'disabled': record.get('disabled', False)
                        })
                        found = True
                    else:
                        updated_records.append(record)
                
                if not found:
                    raise PowerDNSNotFoundError(
                        f"Record not found: {name} {record_type} {old_content}"
                    )
                
                rrset_data = {
                    'rrsets': [{
                        'name': name,
                        'type': record_type,
                        'ttl': ttl or rrset.get('ttl', 3600),
                        'changetype': 'REPLACE',
                        'records': updated_records
                    }]
                }
                
                return self._request(
                    'PATCH',
                    f'servers/{server_id}/zones/{zone_name}',
                    data=rrset_data
                )
        
        raise PowerDNSNotFoundError(
            f"Record set not found: {name} {record_type}"
        )
    
    def delete_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        content: Optional[str] = None,
        server_id: str = 'localhost'
    ) -> Dict[str, Any]:
        """
        Delete a DNS record.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            content: Specific record content to delete (if None, deletes all records of this type)
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone information
        """
        # Ensure name ends with zone name or is FQDN
        if not name.endswith('.'):
            if not name.endswith(zone_name.rstrip('.')):
                name = f"{name}.{zone_name}".rstrip('.')
            name = f"{name}."
        
        if content:
            # Delete specific record
            zone = self.get_zone(zone_name, server_id)
            rrsets = zone.get('rrsets', [])
            
            for rrset in rrsets:
                if rrset.get('name') == name and rrset.get('type') == record_type:
                    records = rrset.get('records', [])
                    remaining_records = [
                        r for r in records
                        if r.get('content') != content
                    ]
                    
                    if len(remaining_records) == len(records):
                        raise PowerDNSNotFoundError(
                            f"Record not found: {name} {record_type} {content}"
                        )
                    
                    if remaining_records:
                        # Update with remaining records
                        rrset_data = {
                            'rrsets': [{
                                'name': name,
                                'type': record_type,
                                'ttl': rrset.get('ttl', 3600),
                                'changetype': 'REPLACE',
                                'records': remaining_records
                            }]
                        }
                    else:
                        # Delete entire rrset
                        rrset_data = {
                            'rrsets': [{
                                'name': name,
                                'type': record_type,
                                'changetype': 'DELETE'
                            }]
                        }
                    
                    return self._request(
                        'PATCH',
                        f'servers/{server_id}/zones/{zone_name}',
                        data=rrset_data
                    )
            
            raise PowerDNSNotFoundError(
                f"Record set not found: {name} {record_type}"
            )
        else:
            # Delete entire rrset
            rrset_data = {
                'rrsets': [{
                    'name': name,
                    'type': record_type,
                    'changetype': 'DELETE'
                }]
            }
            
            return self._request(
                'PATCH',
                f'servers/{server_id}/zones/{zone_name}',
                data=rrset_data
            )

