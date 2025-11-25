from django.urls import path, include
from .versions import get_version_urlpatterns, API_VERSIONS

app_name = "api"

# Build URL patterns for all supported API versions
# Only versioned paths are allowed (e.g., /api/v1/, /api/v2/)
urlpatterns = []

for version in API_VERSIONS.keys():
    urlpatterns.append(
        path(f'{version}/', include((get_version_urlpatterns(version), f'api-{version}'))),
    )

