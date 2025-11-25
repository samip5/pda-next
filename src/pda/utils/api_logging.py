import logging
import time
from typing import Any, Dict, Optional
from uuid import UUID

from django.http import HttpRequest
from django.utils import timezone

from pda.utils.request import get_client_ip

logger = logging.getLogger(__name__)


class APIRequestLog:
    """
    Stores information about an API request for inclusion in responses.
    """
    
    def __init__(self, request: HttpRequest):
        self.request_id: Optional[str] = None
        self.method: str = request.method
        self.path: str = request.path
        self.query_params: Dict[str, Any] = dict(request.GET)
        self.timestamp: str = timezone.now().isoformat()
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
        self.status_code: Optional[int] = None
        self.user_id: Optional[str] = None
        self.user_username: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        
        # Extract request ID if available
        if hasattr(request, 'id'):
            if isinstance(request.id, UUID):
                self.request_id = str(request.id)
            else:
                self.request_id = str(request.id)
        
        # Extract user information
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.user_id = str(request.user.pk) if hasattr(request.user, 'pk') else None
            self.user_username = getattr(request.user, 'username', None)
        
        # Extract IP address using existing utility
        try:
            client_ip = get_client_ip(request)
            self.ip_address = str(client_ip) if client_ip else None
        except (ValueError, Exception):
            # Fallback to simple extraction if utility fails
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                self.ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                self.ip_address = request.META.get('REMOTE_ADDR')
        
        # Extract user agent
        self.user_agent = request.META.get('HTTP_USER_AGENT', None)
    
    def finalize(self, status_code: int) -> None:
        """
        Finalize the log entry with response information.
        
        Args:
            status_code: HTTP status code of the response
        """
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the log entry to a dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the log entry
        """
        return {
            'request_id': self.request_id,
            'method': self.method,
            'path': self.path,
            'query_params': self.query_params,
            'timestamp': self.timestamp,
            'duration_ms': round(self.duration_ms, 2) if self.duration_ms else None,
            'status_code': self.status_code,
            'user_id': self.user_id,
            'user_username': self.user_username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
        }


def get_request_log(request: HttpRequest) -> Optional[APIRequestLog]:
    """
    Get the API request log from the request object.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        APIRequestLog instance or None if not available
    """
    return getattr(request, '_api_request_log', None)


def set_request_log(request: HttpRequest, log: APIRequestLog) -> None:
    """
    Attach an API request log to the request object.
    
    Args:
        request: Django HttpRequest object
        log: APIRequestLog instance
    """
    request._api_request_log = log

