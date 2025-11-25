"""
URL Configuration for PowerDNS API

Note: This file is kept for backwards compatibility, but viewsets
are now registered in the centralized apps.api.urls module using PDARouter.
"""
from django.urls import path, include
from ..routers import PDARouter

from .views import RecordViewSet

router = PDARouter()
router.register(r'', RecordViewSet, basename='record')

app_name = "pdaDnsApi"
urlpatterns = [
    path('', include(router.urls)),
]