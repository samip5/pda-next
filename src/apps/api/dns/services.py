"""
PowerDNS Service Layer

This module provides high-level services for managing zones and records
with PowerDNS, fetching data on-demand from the PowerDNS API.
"""
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from .client import PowerDNSClient, PowerDNSError, PowerDNSNotFoundError
from config import settings as app_settings

if TYPE_CHECKING:
    from .models.zone import Zone

logger = logging.getLogger('pda')


class PowerDNSService:
    """
    Service layer for PowerDNS operations.
    
    Provides methods to fetch and manage zones and records on-demand
    from the PowerDNS API.
    """
    
    def __init__(self, api_url: str | None = None, api_key: str | None = None, timeout: int | None = None, client: Optional[PowerDNSClient] = None):
        """
        Initialize PowerDNS service.
        
        Args:
            api_url: Optional override for API URL
            api_key: Optional override for API key
            timeout: Optional override for timeout
            client: PowerDNS client instance (creates new one if not provided)
        """
        # Fallback to application settings if not provided
        api_url = api_url or app_settings.powerdns_api_url
        api_key = api_key or app_settings.powerdns_api_key
        timeout = timeout or app_settings.powerdns_api_timeout

        self.client = client or PowerDNSClient(api_url, api_key, timeout)
    
    def get_zones(self, server_id: str = 'localhost') -> List[Dict[str, Any]]:
        """
        Fetch all zones from PowerDNS.
        
        Args:
            server_id: Server ID (default: 'localhost')
            
        Returns:
            List of zone dictionaries from PowerDNS API
        """
        try:
            return self.client.get_zones(server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to fetch zones from PowerDNS: {e}")
            return []
    
    def get_zone(self, zone_name: str, server_id: str = 'localhost') -> Optional[Dict[str, Any]]:
        """
        Fetch a specific zone from PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Zone dictionary from PowerDNS API or None if not found
        """
        try:
            return self.client.get_zone(zone_name, server_id)
        except PowerDNSNotFoundError:
            logger.warning(f"Zone {zone_name} not found in PowerDNS")
            return None
        except PowerDNSError as e:
            logger.error(f"Failed to fetch zone {zone_name} from PowerDNS: {e}")
            return None
    
    def get_records(self, zone_name: str, server_id: str = 'localhost') -> List[Dict[str, Any]]| Exception:
        """
        Fetch all records for a zone from PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            
        Returns:
            List of record set dictionaries from PowerDNS API
        """
        try:
            return self.client.get_records(zone_name, server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to fetch records for zone {zone_name} from PowerDNS: {e}")
            return Exception("Unable to fetch records")
    
    def create_zone(
        self,
        zone_name: str,
        nameservers: List[str],
        kind: str = 'Native',
        server_id: str = 'localhost',
        account: str = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]|Exception:
        """
        Create a new zone in PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            nameservers: List of nameserver hostnames
            kind: Zone kind (Native, Master, Slave)
            server_id: Server ID (default: 'localhost')
            account: Account Name
            **kwargs: Additional zone parameters
            
        Returns:
            Created zone dictionary from PowerDNS API or None on error
        """
        try:
            return self.client.create_zone(zone_name, nameservers, kind, server_id, account, **kwargs)
        except PowerDNSError as e:
            logger.error(f"Failed to create zone {zone_name} in PowerDNS: {e}")
            return Exception(PowerDNSError)
    
    def update_zone(
        self,
        zone_name: str,
        server_id: str = 'localhost',
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update a zone in PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            **kwargs: Zone parameters to update
            
        Returns:
            Updated zone dictionary from PowerDNS API or None on error
        """
        try:
            return self.client.update_zone(zone_name, server_id, **kwargs)
        except PowerDNSError as e:
            logger.error(f"Failed to update zone {zone_name} in PowerDNS: {e}")
            return None
    
    def delete_zone(self, zone_name: str, server_id: str = 'localhost') -> bool:
        """
        Delete a zone from PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            server_id: Server ID (default: 'localhost')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_zone(zone_name, server_id)
            logger.info(f"Deleted zone {zone_name} from PowerDNS")
            return True
        except PowerDNSNotFoundError:
            logger.warning(f"Zone {zone_name} already deleted from PowerDNS")
            return True
        except PowerDNSError as e:
            logger.error(f"Failed to delete zone {zone_name} from PowerDNS: {e}")
            return False
    
    def create_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        content: str,
        ttl: int = 3600,
        server_id: str = 'localhost'
    ) -> Optional[Dict[str, Any]]|Exception:
        """
        Create a new DNS record in PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            content: Record content
            ttl: Time to live in seconds
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone dictionary from PowerDNS API or Exception on error
        """
        try:
            return self.client.create_record(zone_name, name, record_type, content, ttl, server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to create record {name} {record_type} in zone {zone_name}: {e}")
            return Exception(PowerDNSError)
    
    def update_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        old_content: str,
        new_content: str,
        ttl: Optional[int] = None,
        server_id: str = 'localhost'
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing DNS record in PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            old_content: Current record content
            new_content: New record content
            ttl: Time to live in seconds (optional)
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone dictionary from PowerDNS API or None on error
        """
        try:
            return self.client.update_record(
                zone_name, name, record_type, old_content, new_content, ttl, server_id
            )
        except PowerDNSError as e:
            logger.error(f"Failed to update record {name} {record_type} in zone {zone_name}: {e}")
            return None
    
    def delete_record(
        self,
        zone_name: str,
        name: str,
        record_type: str,
        content: Optional[str] = None,
        server_id: str = 'localhost'
    ) -> Optional[Dict[str, Any]]:
        """
        Delete a DNS record from PowerDNS.
        
        Args:
            zone_name: Zone name (e.g., 'example.com.')
            name: Record name (relative to zone or FQDN)
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            content: Specific record content to delete (if None, deletes all records of this type)
            server_id: Server ID (default: 'localhost')
            
        Returns:
            Updated zone dictionary from PowerDNS API or None on error
        """
        try:
            return self.client.delete_record(zone_name, name, record_type, content, server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to delete record {name} {record_type} from zone {zone_name}: {e}")
            return None

    def dnssec_keys(
        self,
        zone_name: str,
        keytype: str = 'ksk',
        server_id: str = 'localhost'
    ) -> Optional[Dict[str, Any]]|Exception:
        try:
            return self.client.dnssec_keys(zone_name, keytype, server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to create dnssec keys ({keytype}) for zone {zone_name}: {e}")
            return Exception(PowerDNSError("Unable to create dnssec keys"))

    def disable_dnssec(
        self,
        zone_name: str,
        server_id: str = 'localhost'
    ) -> Optional[Dict[str, Any]]|Exception:
        try:
            return self.client.disable_DNSSEC(zone_name, server_id)
        except PowerDNSError as e:
            logger.error(f"Failed to disable dnssec for zone {zone_name}: {e}")
            return Exception(PowerDNSError("Unable to disable DNSSEC"))
