from typing import Dict, Any
from django.urls import path, include
from .routers import PDARouter

# Import all viewsets
from .accounts.views import AccountViewSet
from .dns.views import RecordViewSet
from .templates.views import TemplateViewSet


def get_v1_urlpatterns() -> list:
    """
    Returns URL patterns for API v1.
    
    To add a new version (e.g., v2):
    1. Create a get_v2_urlpatterns() function
    2. Register it in API_VERSIONS below
    3. Add 'v2' to REST_FRAMEWORK['ALLOWED_VERSIONS'] in settings
    """
    router = PDARouter()
    
    # Register all viewsets for v1
    router.register(r'accounts', AccountViewSet, basename='account')
    router.register(r'dns', RecordViewSet, basename='dns')
    router.register(r'templates', TemplateViewSet, basename='template')
    
    return [
        path('', include(router.urls)),
    ]


# Map of API versions to their URL pattern functions
API_VERSIONS: Dict[str, Any] = {
    'v1': get_v1_urlpatterns,
    # Add new versions here:
    # 'v2': get_v2_urlpatterns,
}


def get_version_urlpatterns(version: str) -> list:
    """
    Get URL patterns for a specific API version.
    
    Args:
        version: The API version (e.g., 'v1', 'v2')
        
    Returns:
        List of URL patterns for the specified version
        
    Raises:
        ValueError: If the version is not supported
    """
    if version not in API_VERSIONS:
        raise ValueError(f"API version '{version}' is not supported. Available versions: {list(API_VERSIONS.keys())}")
    
    return API_VERSIONS[version]()

