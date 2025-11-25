from rest_framework.request import Request


def get_api_version(request: Request) -> str:
    """
    Get the API version from the request.
    
    Args:
        request: The DRF request object
        
    Returns:
        The API version string (e.g., 'v1', 'v2')
        
    Example:
        ```python
        from apps.api.versioning import get_api_version
        
        class MyViewSet(viewsets.ModelViewSet):
            def list(self, request):
                version = get_api_version(request)
                if version == 'v1':
                    # v1 behavior
                    pass
                elif version == 'v2':
                    # v2 behavior
                    pass
        ```
    """
    if hasattr(request, 'version'):
        return request.version
    return 'v1'  # Default fallback


def is_version(request: Request, version: str) -> bool:
    """
    Check if the request is for a specific API version.
    
    Args:
        request: The DRF request object
        version: The version to check (e.g., 'v1', 'v2')
        
    Returns:
        True if the request is for the specified version
        
    Example:
        ```python
        from apps.api.versioning import is_version
        
        if is_version(request, 'v2'):
            # v2-specific logic
            pass
        ```
    """
    return get_api_version(request) == version

